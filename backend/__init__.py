from flask import Flask, render_template, session, redirect, url_for, request #-new request

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

db = SQLAlchemy()


def create_app():
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), "..", "templates"),
        static_folder=os.path.join(os.path.dirname(__file__), "..", "static")
    )

    app.config["SECRET_KEY"] = "rosemary-secret"
    app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:2020@localhost/rosemary_store"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    # -------------------
    # LOGIN MANAGER
    # -------------------
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    from .models import Employee, Customer, Product

    @login_manager.user_loader
    def load_user(user_id):
        return Employee.query.get(int(user_id)) or Customer.query.get(int(user_id))

    # -------------------
    # LANDING PAGE
    # -------------------
    @app.route("/")
    def landing():
        session.pop('_flashes', None)
        return render_template("landing.html")

    # -------------------
    # CUSTOMER SHOP
    # -------------------
    @app.route("/shop")
    def shop():
        if session.get("user_type") != "customer":
            return redirect(url_for("auth.login"))

        #---------new updated
        q = request.args.get("q", "").strip()
        query = Product.query
        if q:
            query = query.filter(Product.Name.ilike(f"%{q}%"))
        products = query.all()
        return render_template("shop.html", products=products, q=q)#--till here

        return render_template("shop.html", products=products)

    # -------------------
    # EMPLOYEE PRODUCTS
    # -------------------
    @app.route("/products")
    def products():
        if session.get("user_type") != "employee":
            return redirect(url_for("auth.login"))

        # ----------------updated
        q = request.args.get("q", "").strip()
        query = Product.query
        if q:
            query = query.filter(Product.Name.ilike(f"%{q}%"))
        products = query.all()
        return render_template("products.html", products=products, q=q)#till here

        return render_template("products.html", products=products)

    # -------------------
    # REGISTER BLUEPRINTS
    # -------------------
    from .auth import auth
    app.register_blueprint(auth)

    from .product_routes import product_bp
    app.register_blueprint(product_bp)

    from .cart_routes import cart_bp
    app.register_blueprint(cart_bp)

    from .queries import queries_bp
    app.register_blueprint(queries_bp)

    # -------------------
    # DB INIT
    # -------------------
    with app.app_context():
        db.create_all()

    return app