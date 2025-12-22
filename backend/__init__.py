from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os
db = SQLAlchemy()


def create_app():
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), "..", "templates"),
        static_folder=os.path.join(os.path.dirname(__file__), "..", "static")
    )

    app.config["SECRET_KEY"] = "1234abd"
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        "mysql+pymysql://root:2020@localhost/rosemary_store"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)


    from .models import Product

    # ========================
    # ROUTES
    # ========================

    # MAIN PAGE + LIST PRODUCTS
    @app.route("/")
    @app.route("/products")
    def products():
        all_products = Product.query.all()
        return render_template("products.html", products=all_products)

    # ADD PRODUCT
    @app.route("/product/add", methods=["POST"])
    def add_product():
        product = Product(
            Name=request.form["name"],
            Price=float(request.form["price"]),
            Barcode=request.form["barcode"],
            Quantity=int(request.form["quantity"])
        )
        db.session.add(product)
        db.session.commit()
        return redirect(url_for("products"))

    # UPDATE PRODUCT
    @app.route("/product/update/<int:pid>", methods=["POST"])
    def update_product(pid):
        product = Product.query.get_or_404(pid)

        product.Name = request.form["name"]
        product.Price = float(request.form["price"])
        product.Barcode = request.form["barcode"]
        product.Quantity = int(request.form["quantity"])

        db.session.commit()
        return redirect(url_for("products"))

    # DELETE PRODUCT
    @app.route("/product/delete/<int:pid>")
    def delete_product(pid):
        product = Product.query.get_or_404(pid)
        db.session.delete(product)
        db.session.commit()
        return redirect(url_for("products"))

    # ========================

    with app.app_context():
        db.create_all()

    return app
