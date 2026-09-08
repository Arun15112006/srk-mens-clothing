from flask import Flask, render_template

app = Flask(__name__)

products = [
    {
        "id": 1,
        "name": "Red Baggy Shirt",
        "price": 799,
        "category": "Baggy Shirts",
        "images": [
            "Baggy Shirts red.jpg"
        ],
        "sizes": ["S", "M", "L", "XL", "XXL"]
    },

    {
        "id": 2,
        "name": "Brown Baggy Shirt",
        "price": 799,
        "category": "Baggy Shirts",
        "images": [
            "Baggy shirt brown.jpg"
        ],
        "sizes": ["S", "M", "L", "XL", "XXL"]
    },

    {
        "id": 3,
        "name": "Green Baggy Shirt",
        "price": 799,
        "category": "Baggy Shirts",
        "images": [
            "Baggy shirt green.jpg"
        ],
        "sizes": ["S", "M", "L", "XL", "XXL"]
    },

    {
        "id": 4,
        "name": "Black Baggy Pant",
        "price": 999,
        "category": "Baggy Pants",
        "images": [
            "Baggy pant black.jpg"
        ],
        "sizes": ["28", "30", "32", "34", "36", "38"]
    },

    {
        "id": 5,
        "name": "Brown Baggy Pant",
        "price": 999,
        "category": "Baggy Pants",
        "images": [
            "Baggy pant brown.jpg"
        ],
        "sizes": ["28", "30", "32", "34", "36", "38"]
    },

    {
        "id": 6,
        "name": "Grey Polo T-Shirt",
        "price": 599,
        "category": "Polo T-Shirts",
        "images": [
            "Polo tshirt grey.jpg"
        ],
        "sizes": ["S", "M", "L", "XL", "XXL"]
    },

    {
        "id": 7,
        "name": "Light Blue Polo T-Shirt",
        "price": 599,
        "category": "Polo T-Shirts",
        "images": [
            "Polo tshirt light blue.jpg"
        ],
        "sizes": ["S", "M", "L", "XL", "XXL"]
    },

    {
        "id": 8,
        "name": "Navy Blue Polo T-Shirt",
        "price": 599,
        "category": "Polo T-Shirts",
        "images": [
            "Polo tshirt navy blue.jpg"
        ],
        "sizes": ["S", "M", "L", "XL", "XXL"]
    },

    {
        "id": 9,
        "name": "Red Polo T-Shirt",
        "price": 599,
        "category": "Polo T-Shirts",
        "images": [
            "Polo tshirt red.jpg"
        ],
        "sizes": ["S", "M", "L", "XL", "XXL"]
    },

    {
        "id": 10,
        "name": "White Polo T-Shirt",
        "price": 599,
        "category": "Polo T-Shirts",
        "images": [
            "Polo tshirt white.jpg"
        ],
        "sizes": ["S", "M", "L", "XL", "XXL"]
    }
]


@app.route("/")
def home():
    return render_template("index.html", products=products)


@app.route("/products")
def product_list():
    return products


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
