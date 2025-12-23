from flask import current_app

from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime

db = SQLAlchemy()

def create_app():
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), "..", "templates"),
        static_folder=os.path.join(os.path.dirname(__file__), "..", "static")
    )

    app.config["SECRET_KEY"] = "1234abd"
    app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:2020@localhost/rosemary_store"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    from .models import Product, Orders, OrderItem, Customer, Employee

    # -------------------------
    # Seed initial products
    # -------------------------
    def seed_products_if_empty():
        if Product.query.count() > 0:
            return

        initial = [
            {"Name": "Rice",   "Price": 8.50, "Barcode": "RICE001",  "Quantity": 100, "Image": "rice.jpg"},
            {"Name": "Salt",   "Price": 2.00, "Barcode": "SALT001",  "Quantity": 200, "Image": "salt.jpg"},
            {"Name": "Sugar",  "Price": 4.50, "Barcode": "SUGR001",  "Quantity": 150, "Image": "sugar.jpg"},
            {"Name": "Candy",  "Price": 1.25, "Barcode": "CAND001",  "Quantity": 300, "Image": "candy.jpg"},
            {"Name": "Water",  "Price": 1.00, "Barcode": "WATR001",  "Quantity": 500, "Image": "water.jpg"},
            {"Name": "Tea",    "Price": 6.00, "Barcode": "TEA0001",  "Quantity": 80,  "Image": "tea.jpg"},
        ]

        for p in initial:
            db.session.add(Product(**p))
        db.session.commit()

    # -------------------------
    # Helpers (Cart)
    # -------------------------
    def get_cart():
        # cart format in session: {"1": 2, "5": 1}  => product_id : qty
        return session.get("cart", {})

    def save_cart(cart):
        session["cart"] = cart
        session.modified = True

    # ========================
    # ROUTES
    # ========================

    # ✅ SHOP HOME (Customer view)
    @app.route("/")
    def shop_home():
        products = Product.query.all()
        return render_template("shop.html", products=products)

    # ✅ PRODUCT DETAILS + ADD TO CART
    @app.route("/shop/<int:pid>")
    def product_details(pid):
        p = Product.query.get_or_404(pid)

        image_path = os.path.join(
            current_app.root_path,
            "static",
            "products",
            p.Image if p.Image else ""
        )

        if not p.Image or not os.path.exists(image_path):
            p.Image = "placeholder.jpg"

        return render_template("product_details.html", p=p)

    @app.route("/cart/add/<int:pid>", methods=["POST"])
    def cart_add(pid):
        qty = int(request.form.get("quantity", 1))

        cart = session.get("cart", {})
        cart[str(pid)] = cart.get(str(pid), 0) + qty

        session["cart"] = cart
        session.modified = True

        return redirect(url_for("cart_view"))

    @app.route("/cart")
    def cart_view():
        cart = session.get("cart", {})

        items = []
        total = 0

        for pid_str, qty in cart.items():
            p = Product.query.get(int(pid_str))
            if p:
                qty = int(qty)
                items.append((p, qty))
                total += p.Price * qty

        return render_template("cart.html", items=items, total=total)

    @app.route("/cart/update", methods=["POST"])
    def cart_update():
        cart = get_cart()

        for key, value in request.form.items():
            if not key.startswith("qty_"):
                continue
            pid = key.replace("qty_", "")
            try:
                qty = int(value)
            except:
                qty = 0

            p = Product.query.get(int(pid))
            if not p:
                cart.pop(pid, None)
                continue

            if qty <= 0:
                cart.pop(pid, None)
            else:
                if qty > p.Quantity:
                    qty = p.Quantity
                cart[pid] = qty

        save_cart(cart)
        flash("Cart updated.", "success")
        return redirect(url_for("cart_view"))

    @app.route("/cart/remove/<int:pid>")
    def cart_remove(pid):
        cart = session.get("cart", {})
        cart.pop(str(pid), None)
        session["cart"] = cart
        session.modified = True
        return redirect(url_for("cart_view"))

    @app.route("/checkout", methods=["GET", "POST"])
    def checkout():
        cart = session.get("cart", {})
        if not cart:
            return redirect(url_for("shop_home"))

        items = []
        total = 0
        total_qty = 0

        for pid_str, qty in cart.items():
            p = Product.query.get(int(pid_str))
            qty = int(qty)
            items.append((p, qty))
            total += p.Price * qty
            total_qty += qty

        if request.method == "GET":
            return render_template("checkout.html", total=total)

        # ✅ POST — THIS PART INSERTS INTO DB
        order = Orders(
            Cust_ID=None,
            Emp_ID=None,
            Quantity=total_qty,
            Price=total,
            Discount=0,
            Date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        db.session.add(order)
        db.session.flush()  # get Order_ID

        for p, qty in items:
            db.session.add(
                OrderItem(
                    Order_ID=order.Order_ID,
                    Product_ID=p.Product_ID,
                    Quantity=qty
                )
            )
            p.Quantity -= qty

        db.session.commit()
        session["cart"] = {}

        return redirect(url_for("shop_home"))


    @app.route("/products")
    def products():
        all_products = Product.query.all()
        return render_template("products.html", products=all_products)

    @app.route("/product/add", methods=["POST"])
    def add_product():
        product = Product(
            Name=request.form["name"],
            Price=float(request.form["price"]),
            Barcode=request.form["barcode"],
            Quantity=int(request.form["quantity"]),
            Image=request.form.get("image", None)  # ✅ allow optional image filename
        )
        db.session.add(product)
        db.session.commit()
        return redirect(url_for("products"))

    @app.route("/product/update/<int:pid>", methods=["POST"])
    def update_product(pid):
        product = Product.query.get_or_404(pid)
        product.Name = request.form["name"]
        product.Price = float(request.form["price"])
        product.Barcode = request.form["barcode"]
        product.Quantity = int(request.form["quantity"])
        product.Image = request.form.get("image", product.Image)
        db.session.commit()
        return redirect(url_for("products"))

    @app.route("/product/delete/<int:pid>")
    def delete_product(pid):
        product = Product.query.get_or_404(pid)
        db.session.delete(product)
        db.session.commit()
        return redirect(url_for("products"))

    # ========================
    with app.app_context():
        db.create_all()
        seed_products_if_empty()

    return app
