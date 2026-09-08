from flask import Flask, render_template, jsonify

app = Flask(__name__)

products = [
    {
        "id": 1,
        "name": "Classic Black T-Shirt",
        "price": 499,
        "category": "T-Shirts",
        "emoji": "👕",
        "sizes": ["S", "M", "L", "XL", "XXL"]
    },
    {
        "id": 2,
        "name": "Premium White Shirt",
        "price": 899,
        "category": "Shirts",
        "emoji": "👔",
        "sizes": ["S", "M", "L", "XL", "XXL"]
    },
    {
        "id": 3,
        "name": "Blue Denim Jeans",
        "price": 1299,
        "category": "Jeans",
        "emoji": "👖",
        "sizes": ["28", "30", "32", "34", "36", "38"]
    },
    {
        "id": 4,
        "name": "Casual Black Shirt",
        "price": 799,
        "category": "Shirts",
        "emoji": "👔",
        "sizes": ["S", "M", "L", "XL", "XXL"]
    },
    {
        "id": 5,
        "name": "Oversized Black T-Shirt",
        "price": 599,
        "category": "T-Shirts",
        "emoji": "👕",
        "sizes": ["S", "M", "L", "XL", "XXL"]
    },
    {
        "id": 6,
        "name": "Slim Fit Jeans",
        "price": 1499,
        "category": "Jeans",
        "emoji": "👖",
        "sizes": ["28", "30", "32", "34", "36", "38"]
    }
]


@app.route("/")
def home():
    return render_template("index.html", products=products)


@app.route("/products")
def product_list():
    return jsonify(products)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
