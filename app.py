from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
import uuid
import pg8000.dbapi
import cloudinary
import cloudinary.uploader
from urllib.parse import urlparse

app = Flask(__name__)
cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key=os.environ.get("CLOUDINARY_API_KEY"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET")
)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "srk-development-secret"
)


# STORAGE

if os.environ.get("RENDER"):
    STORAGE_FOLDER = "/opt/render/project/src/storage"
else:
    STORAGE_FOLDER = "storage"

DATABASE = os.path.join(
    STORAGE_FOLDER,
    "srk.db"
)

UPLOAD_FOLDER = os.path.join(
    STORAGE_FOLDER,
    "uploads"
)

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024


# DATABASE

USE_POSTGRES = bool(
    os.environ.get("DATABASE_URL")
)


class PostgresResult:

    def __init__(self, cursor):
        self.cursor = cursor

    def fetchone(self):
        row = self.cursor.fetchone()

        if row is None:
            return None

        columns = [
            column[0]
            for column in self.cursor.description
        ]

        return dict(zip(columns, row))

    def fetchall(self):
        rows = self.cursor.fetchall()

        if not rows:
            return []

        columns = [
            column[0]
            for column in self.cursor.description
        ]

        return [
            dict(zip(columns, row))
            for row in rows
        ]


class PostgresConnection:

    def __init__(self, url):

        parsed = urlparse(url)

        self.conn = pg8000.dbapi.connect(
            user=parsed.username,
            password=parsed.password,
            host=parsed.hostname,
            port=parsed.port or 5432,
            database=parsed.path.lstrip("/")
        )

    def execute(self, query, params=()):

        query = query.replace("?", "%s")

        cursor = self.conn.cursor()

        cursor.execute(
            query,
            params
        )

        return PostgresResult(cursor)

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()


def get_db():

    database_url = os.environ.get(
        "DATABASE_URL"
    )

    if database_url:
        return PostgresConnection(
            database_url
        )

    conn = sqlite3.connect(
        DATABASE
    )

    conn.row_factory = sqlite3.Row

    return conn


def init_db():

    conn = get_db()

    if USE_POSTGRES:

        conn.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                category TEXT NOT NULL,
                sizes TEXT NOT NULL,
                description TEXT DEFAULT '',
                images TEXT DEFAULT ''
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id SERIAL PRIMARY KEY,
                customer_name TEXT NOT NULL,
                phone TEXT NOT NULL,
                address TEXT NOT NULL,
                product_name TEXT NOT NULL,
                size TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                total REAL NOT NULL,
                status TEXT DEFAULT 'New',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            ALTER TABLE orders
            ADD COLUMN IF NOT EXISTS customer_id INTEGER
        """)

    else:

        conn.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                category TEXT NOT NULL,
                sizes TEXT NOT NULL,
                description TEXT DEFAULT '',
                images TEXT DEFAULT ''
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                phone TEXT NOT NULL,
                address TEXT NOT NULL,
                product_name TEXT NOT NULL,
                size TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                total REAL NOT NULL,
                status TEXT DEFAULT 'New',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

    conn.commit()
    conn.close()


def get_products():

    conn = get_db()

    products = conn.execute(
        "SELECT * FROM products ORDER BY id DESC"
    ).fetchall()

    conn.close()

    result = []

    for product in products:

        item = dict(product)

        item["sizes"] = [
            x.strip()
            for x in item["sizes"].split(",")
            if x.strip()
        ]

        item["images"] = [
            x.strip()
            for x in item["images"].split(",")
            if x.strip()
        ]

        result.append(item)

    return result


# STORE

@app.route("/")
def home():

    products = get_products()

    categories = sorted(
        set(
            product["category"]
            for product in products
        )
    )

    return render_template(
        "index.html",
        products=products,
        categories=categories
    )


# ADMIN

ADMIN_USERNAME = os.environ.get(
    "ADMIN_USERNAME",
    "admin"
)

ADMIN_PASSWORD = os.environ.get(
    "ADMIN_PASSWORD",
    "srkadmin123"
)


@app.route(
    "/admin/login",
    methods=["GET", "POST"]
)
def admin_login():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        )

        password = request.form.get(
            "password",
            ""
        )

        if (
            username == ADMIN_USERNAME
            and password == ADMIN_PASSWORD
        ):

            session["admin"] = True

            return redirect(
                url_for("admin")
            )

        flash(
            "Invalid username or password."
        )

    return render_template(
        "admin_login.html"
    )


@app.route("/admin/logout")
def admin_logout():

    session.pop(
        "admin",
        None
    )

    return redirect(
        url_for("admin_login")
    )


def admin_required():

    return session.get(
        "admin"
    ) is True


@app.route("/admin")
def admin():

    if not admin_required():

        return redirect(
            url_for("admin_login")
        )

    conn = get_db()

    total_orders = conn.execute(
        "SELECT COUNT(*) AS count FROM orders"
    ).fetchone()["count"]

    new_orders = conn.execute(
        "SELECT COUNT(*) AS count FROM orders WHERE status='New'"
    ).fetchone()["count"]

    shipped_orders = conn.execute(
        "SELECT COUNT(*) AS count FROM orders WHERE status='Shipped'"
    ).fetchone()["count"]

    conn.close()

    products = get_products()

    return render_template(
        "admin.html",
        products=products,
        total_orders=total_orders,
        new_orders=new_orders,
        shipped_orders=shipped_orders
    )


# ADD PRODUCT

@app.route(
    "/admin/add",
    methods=["POST"]
)
def add_product():

    if not admin_required():

        return redirect(
            url_for("admin_login")
        )

    name = request.form.get(
        "name",
        ""
    ).strip()

    price = request.form.get(
        "price",
        "0"
    )

    category = request.form.get(
        "category",
        ""
    ).strip()

    sizes = request.form.get(
        "sizes",
        ""
    ).strip()

    description = request.form.get(
        "description",
        ""
    ).strip()

    if not name or not category:

        flash(
            "Product name and category are required."
        )

        return redirect(
            url_for("admin")
        )

    try:
        price = float(price)

    except ValueError:

        flash("Invalid price.")

        return redirect(
            url_for("admin")
        )

    saved_images = []

    files = request.files.getlist(
        "images"
    )

    for file in files:

        if file and file.filename:

            extension = os.path.splitext(
                file.filename
            )[1].lower()

            if extension not in [
                ".jpg",
                ".jpeg",
                ".png",
                ".webp"
            ]:
                continue

            filename = (
                uuid.uuid4().hex
                + extension
            )

            filename = secure_filename(
                filename
            )

            result = cloudinary.uploader.upload(
            file,
            folder="srk-products"
            )

            saved_images.append(
            result["secure_url"]
            )

    conn = get_db()

    conn.execute(
        """
        INSERT INTO products
        (name, price, category, sizes, description, images)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            name,
            price,
            category,
            sizes,
            description,
            ",".join(saved_images)
        )
    )

    conn.commit()
    conn.close()

    flash(
        "Product added successfully."
    )

    return redirect(
        url_for("admin")
    )


# EDIT PRODUCT

@app.route(
    "/admin/edit/<int:product_id>",
    methods=["GET", "POST"]
)
def edit_product(product_id):

    if not admin_required():

        return redirect(
            url_for("admin_login")
        )

    conn = get_db()

    product = conn.execute(
        "SELECT * FROM products WHERE id=?",
        (product_id,)
    ).fetchone()

    if not product:

        conn.close()

        flash(
            "Product not found."
        )

        return redirect(
            url_for("admin")
        )

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        price = request.form.get(
            "price",
            "0"
        )

        category = request.form.get(
            "category",
            ""
        ).strip()

        sizes = request.form.get(
            "sizes",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        try:
            price = float(price)

        except ValueError:

            conn.close()

            flash(
                "Invalid price."
            )

            return redirect(
                url_for(
                    "edit_product",
                    product_id=product_id
                )
            )

        old_images = [
            x.strip()
            for x in product["images"].split(",")
            if x.strip()
        ]

        new_images = []

        files = request.files.getlist(
            "images"
        )

        for file in files:

            if file and file.filename:

                extension = os.path.splitext(
                    file.filename
                )[1].lower()

                if extension not in [
                    ".jpg",
                    ".jpeg",
                    ".png",
                    ".webp"
                ]:
                    continue

                filename = (
                    uuid.uuid4().hex
                    + extension
                )

                filename = secure_filename(
                    filename
                )

                file.save(
                    os.path.join(
                        UPLOAD_FOLDER,
                        filename
                    )
                )

                new_images.append(
                    filename
                )

        if new_images:

            for image in old_images:

                path = os.path.join(
                    UPLOAD_FOLDER,
                    image
                )

                if os.path.exists(path):

                    try:
                        os.remove(path)

                    except OSError:
                        pass

            images = new_images

        else:

            images = old_images

        conn.execute(
            """
            UPDATE products
            SET name=?,
                price=?,
                category=?,
                sizes=?,
                description=?,
                images=?
            WHERE id=?
            """,
            (
                name,
                price,
                category,
                sizes,
                description,
                ",".join(images),
                product_id
            )
        )

        conn.commit()
        conn.close()

        flash(
            "Product updated successfully."
        )

        return redirect(
            url_for("admin")
        )

    data = dict(product)

    data["sizes"] = [
        x.strip()
        for x in data["sizes"].split(",")
        if x.strip()
    ]

    data["images"] = [
        x.strip()
        for x in data["images"].split(",")
        if x.strip()
    ]

    conn.close()

    return render_template(
        "edit_product.html",
        product=data
    )


# DELETE PRODUCT

@app.route(
    "/admin/delete/<int:product_id>",
    methods=["POST"]
)
def delete_product(product_id):

    if not admin_required():

        return redirect(
            url_for("admin_login")
        )

    conn = get_db()

    product = conn.execute(
        "SELECT * FROM products WHERE id=?",
        (product_id,)
    ).fetchone()

    if product:

        images = [
            x.strip()
            for x in product["images"].split(",")
            if x.strip()
        ]

        for image in images:

            path = os.path.join(
                UPLOAD_FOLDER,
                image
            )

            if os.path.exists(path):

                try:
                    os.remove(path)

                except OSError:
                    pass

        conn.execute(
            "DELETE FROM products WHERE id=?",
            (product_id,)
        )

        conn.commit()

    conn.close()

    flash(
        "Product deleted."
    )

    return redirect(
        url_for("admin")
    )


# CUSTOMER ORDER

@app.route(
    "/order",
    methods=["POST"]
)
def create_order():

    customer_id = session.get("customer_id")

    if not customer_id:
        flash("Please login before placing your order.")
        return redirect(url_for("customer_login"))

    customer_name = request.form.get(
        "customer_name",
        ""
    ).strip()

    phone = request.form.get(
        "phone",
        ""
    ).strip()

    address = request.form.get(
        "address",
        ""
    ).strip()

    product_name = request.form.get(
        "product_name",
        ""
    ).strip()

    size = request.form.get(
        "size",
        "Multiple"
    ).strip()

    quantity = request.form.get(
        "quantity",
        "1"
    )

    total = request.form.get(
        "total",
        "0"
    )

    if not customer_name or not phone or not address:
        flash("Please enter your customer details.")
        return redirect(url_for("home"))

    try:
        quantity = int(quantity)
        total = float(total)
    except ValueError:
        flash("Invalid order details.")
        return redirect(url_for("home"))

    conn = get_db()

    conn.execute(
        """
        INSERT INTO orders
        (
            customer_name,
            phone,
            address,
            product_name,
            size,
            quantity,
            total,
            customer_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            customer_name,
            phone,
            address,
            product_name,
            size,
            quantity,
            total,
            customer_id
        )
    )

    conn.commit()
    conn.close()

    return redirect(
        url_for("order_success")
    )


@app.route("/register", methods=["GET", "POST"])
def customer_register():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        if not name:
            flash("Please enter your name.")
            return redirect(url_for("customer_register"))

        if not email and not phone:
            flash("Please enter your email or mobile number.")
            return redirect(url_for("customer_register"))

        if len(password) < 6:
            flash("Password must be at least 6 characters.")
            return redirect(url_for("customer_register"))

        conn = get_db()

        existing = None

        if email:
            existing = conn.execute(
                "SELECT id FROM customers WHERE LOWER(email) = ?",
                (email,)
            ).fetchone()

        if not existing and phone:
            existing = conn.execute(
                "SELECT id FROM customers WHERE phone = ?",
                (phone,)
            ).fetchone()

        if existing:
            conn.close()
            flash(
                "An account already exists with that email or mobile number."
            )
            return redirect(url_for("customer_login"))

        password_hash = generate_password_hash(password)

        conn.execute(
            """
            INSERT INTO customers
            (
                name,
                email,
                phone,
                password_hash
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                name,
                email or None,
                phone or None,
                password_hash
            )
        )

        conn.commit()

        if email:
            customer = conn.execute(
                """
                SELECT id, name
                FROM customers
                WHERE LOWER(email) = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (email,)
            ).fetchone()
        else:
            customer = conn.execute(
                """
                SELECT id, name
                FROM customers
                WHERE phone = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (phone,)
            ).fetchone()

        conn.close()

        if not customer:
            flash("Account creation failed. Please try again.")
            return redirect(url_for("customer_register"))

        session["customer_id"] = customer["id"]
        session["customer_name"] = customer["name"]

        flash("Account created successfully!")

        return redirect(url_for("home"))

    return render_template("customer_register.html")


@app.route("/login", methods=["GET", "POST"])
def customer_login():

    if request.method == "POST":

        identifier = request.form.get(
            "identifier",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        if not identifier or not password:
            flash("Please enter your email/mobile number and password.")
            return redirect(url_for("customer_login"))

        conn = get_db()

        customer = conn.execute(
            """
            SELECT *
            FROM customers
            WHERE LOWER(email) = ?
               OR phone = ?
            LIMIT 1
            """,
            (
                identifier.lower(),
                identifier
            )
        ).fetchone()

        conn.close()

        if not customer:
            flash("Invalid email/mobile number or password.")
            return redirect(url_for("customer_login"))

        if not check_password_hash(
            customer["password_hash"],
            password
        ):
            flash("Invalid email/mobile number or password.")
            return redirect(url_for("customer_login"))

        session["customer_id"] = customer["id"]
        session["customer_name"] = customer["name"]

        flash("Welcome back, " + customer["name"] + "!")

        return redirect(url_for("home"))

    return render_template("customer_login.html")


@app.route("/my-orders")
def my_orders():

    customer_id = session.get("customer_id")

    if not customer_id:
        flash("Please login to view your orders.")
        return redirect(url_for("customer_login"))

    conn = get_db()

    orders = conn.execute(
        """
        SELECT *
        FROM orders
        WHERE customer_id = ?
        ORDER BY id DESC
        """,
        (customer_id,)
    ).fetchall()

    conn.close()

    return render_template(
        "my_orders.html",
        orders=orders
    )


@app.route("/order-success")
def order_success():

    return render_template(
        "order_success.html"
    )


# ADMIN ORDERS

@app.route("/admin/orders")
def admin_orders():

    if not admin_required():

        return redirect(
            url_for("admin_login")
        )

    conn = get_db()

    orders = conn.execute(
        """
        SELECT *
        FROM orders
        ORDER BY id DESC
        """
    ).fetchall()

    conn.close()

    return render_template(
        "orders.html",
        orders=orders
    )


@app.route(
    "/admin/orders/status/<int:order_id>",
    methods=["POST"]
)
def update_order_status(order_id):

    if not admin_required():

        return redirect(
            url_for("admin_login")
        )

    status = request.form.get(
        "status",
        "New"
    )

    allowed = [
        "New",
        "Confirmed",
        "Shipped",
        "Delivered",
        "Cancelled"
    ]

    if status not in allowed:

        status = "New"

    conn = get_db()

    conn.execute(
        """
        UPDATE orders
        SET status=?
        WHERE id=?
        """,
        (
            status,
            order_id
        )
    )

    conn.commit()
    conn.close()

    return redirect(
        url_for("admin_orders")
    )


@app.route(
    "/admin/orders/delete/<int:order_id>",
    methods=["POST"]
)
def delete_order(order_id):

    if not admin_required():

        return redirect(
            url_for("admin_login")
        )

    conn = get_db()

    conn.execute(
        "DELETE FROM orders WHERE id=?",
        (order_id,)
    )

    conn.commit()
    conn.close()

    flash(
        "Order deleted."
    )

    return redirect(
        url_for("admin_orders")
    )


# START

init_db()


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
