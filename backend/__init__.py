from flask import Flask, render_template, session, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os
#from .seed import seed_products


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

    # Import models ONLY after db is ready
    from .models import Employee, Customer, Product

    @login_manager.user_loader
    def load_user(user_id):
        user_type = session.get("user_type")

        if user_type == "employee":
            return Employee.query.get(int(user_id))
        elif user_type == "customer":
            return Customer.query.get(int(user_id))

        # fallback
        return Customer.query.get(int(user_id)) or Employee.query.get(int(user_id))

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

        q = request.args.get("q", "").strip()
        query = Product.query
        if q:
            query = query.filter(Product.Name.ilike(f"%{q}%"))
        products = query.all()

        return render_template("shop.html", products=products, q=q)

    # -------------------
    # EMPLOYEE PRODUCTS
    # -------------------
    @app.route("/products")
    def products():
        if session.get("user_type") != "employee":
            return redirect(url_for("auth.login"))

        q = request.args.get("q", "").strip()
        query = Product.query
        if q:
            query = query.filter(Product.Name.ilike(f"%{q}%"))
        products = query.all()

        return render_template("products.html", products=products, q=q)

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

    #  Register employee orders blueprint INSIDE create_app (prevents circular import)
    from .employee_orders import employee_orders_bp
    app.register_blueprint(employee_orders_bp)

    # -------------------
    # DB INIT
    # -------------------
    with app.app_context():
        db.create_all()

        # import here to avoid circular import
        from .seed import seed_products
        seed_products()

    return app
