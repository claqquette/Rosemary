from . import db
from flask_login import UserMixin


# ===========================
# Manufacturer Table
# ===========================
class Manufacturer(db.Model):
    __tablename__ = 'Manufacturer'

    Man_ID = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    Name = db.Column(db.String(120))
    Address = db.Column(db.String(200))
    Email = db.Column(db.String(120))

    # One manufacturer → many products
    products = db.relationship(
        'Product',
        backref=db.backref('manufacturer'),
        lazy=True
    )


# ===========================
# Product Table
# ===========================
class Product(db.Model):
    __tablename__ = 'Product'

    Product_ID = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    Man_ID = db.Column(
        db.Integer,
        db.ForeignKey('Manufacturer.Man_ID', onupdate='CASCADE'),
        nullable=True
    )

    Name = db.Column(db.String(120))
    Price = db.Column(db.Float)
    Barcode = db.Column(db.String(120))
    Quantity = db.Column(db.Integer)

    # ✅ NEW: image filename stored in DB (ex: "rice.jpg")
    Image = db.Column(db.String(255), nullable=True)

    warehouse_item = db.relationship(
        'WarehouseItem',
        backref=db.backref('product', uselist=False),
        uselist=False
    )

    order_items = db.relationship(
        'OrderItem',
        backref=db.backref('product'),
        lazy=True
    )



# ===========================
# WarehouseItem Table (1–1 with Product)
# ===========================
class WarehouseItem(db.Model):
    __tablename__ = 'WarehouseItem'

    WI_ID = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    Product_ID = db.Column(
        db.Integer,
        db.ForeignKey('Product.Product_ID', onupdate='CASCADE', ondelete='CASCADE'),
        unique=True,   # enforce 1–1
        nullable=False
    )
    Quantity = db.Column(db.Integer)


# ===========================
# Customer Table
# ===========================
class Customer(db.Model):
    __tablename__ = 'Customer'

    Cust_ID = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    Phone_Num = db.Column(db.String(50))
    Name = db.Column(db.String(120))

    # One customer → many orders
    orders = db.relationship(
        'Orders',
        backref=db.backref('customer'),
        lazy=True
    )


# ===========================
# Employee Table (Login User)
# ===========================
class Employee(db.Model, UserMixin):
    __tablename__ = 'Employee'

    Emp_ID = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    Phone_Num = db.Column(db.String(50))
    Name = db.Column(db.String(120))
    Address = db.Column(db.String(200))

    # OPTIONAL login fields (add if you want login system)
    Email = db.Column(db.String(100), unique=True, nullable=True)
    Password = db.Column(db.String(255), nullable=True)

    # One employee → many orders
    orders = db.relationship(
        'Orders',
        backref=db.backref('employee'),
        lazy=True
    )

    def get_id(self):
        # For Flask-Login
        return str(self.Emp_ID)


# ===========================
# Orders Table
# ===========================
class Orders(db.Model):
    __tablename__ = 'Orders'

    Order_ID = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)

    Cust_ID = db.Column(
        db.Integer,
        db.ForeignKey('Customer.Cust_ID', onupdate='CASCADE'),
        nullable=True
    )
    Emp_ID = db.Column(
        db.Integer,
        db.ForeignKey('Employee.Emp_ID', onupdate='CASCADE'),
        nullable=True
    )

    Quantity = db.Column(db.Integer)
    Date = db.Column(db.String(50))      # you can change to db.Date or db.DateTime later
    Price = db.Column(db.Float)
    Discount = db.Column(db.Float)

    # One order → many order items
    order_items = db.relationship(
        'OrderItem',
        backref=db.backref('order'),
        lazy=True
    )


# ===========================
# OrderItem Table (M–N link: Orders ↔ Product)
# ===========================
class OrderItem(db.Model):
    __tablename__ = 'Order_Item'

    Order_ID = db.Column(
        db.Integer,
        db.ForeignKey('Orders.Order_ID', ondelete='CASCADE'),
        primary_key=True
    )
    Product_ID = db.Column(
        db.Integer,
        db.ForeignKey('Product.Product_ID', ondelete='CASCADE'),
        primary_key=True
    )

    Quantity = db.Column(db.Integer, nullable=False)
