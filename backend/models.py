from . import db
from flask_login import UserMixin
from sqlalchemy import func


# MANIFACTURER Table
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


# Product Table
class Product(db.Model):
    __tablename__ = 'Product'

    def get_discount_percent(self) -> int:
        return int(self.Discount_Percent or 0)

    @property
    def discounted_price(self) -> float:
        p = float(self.Price or 0)
        d = self.get_discount_percent()
        return round(p * (1 - d / 100), 2)

    @property
    def discount_amount(self) -> float:
        return round(float(self.Price or 0) - self.discounted_price, 2)

    Product_ID = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)

    Man_ID = db.Column(
        db.Integer,
        db.ForeignKey('Manufacturer.Man_ID', onupdate='CASCADE'),
        nullable=True
    )

    Name = db.Column(db.String(120))
    Price = db.Column(db.Float)
    Barcode = db.Column(db.String(120))

    # Get quantity from warehouse item
    @property
    def stock_qty(self):
        wi = WarehouseItem.query.filter_by(Product_ID=self.Product_ID).first()
        return wi.Quantity if wi and wi.Quantity is not None else 0

    Image = db.Column(db.String(255), nullable=True)
    Discount_Percent = db.Column(db.Integer, default=0)
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


# WarehouseItem Table (1–1 with Product)
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


# Customer Table
class Customer(db.Model, UserMixin):
    __tablename__ = 'Customer'

    Cust_ID = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    Phone_Num = db.Column(db.String(50))
    Name = db.Column(db.String(120))
    Email = db.Column(db.String(50), unique=True)
    Password = db.Column(db.String(50))

    # One customer → many orders
    orders = db.relationship(
        'Orders',
        backref=db.backref('customer'),
        lazy=True
    )

    def get_id(self):
        # For Flask-Login
        return str(self.Cust_ID)


# Employee Table (Login User)
class Employee(db.Model, UserMixin):
    __tablename__ = 'Employee'

    Emp_ID = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    Phone_Num = db.Column(db.String(50))
    Name = db.Column(db.String(120))
    Address = db.Column(db.String(200))

    Email = db.Column(db.String(50), unique=True)
    Password = db.Column(db.String(50))

    # One employee to many orders
    orders = db.relationship(
        'Orders',
        backref=db.backref('employee'),
        lazy=True
    )

    def get_id(self):
        # For Flask-Login
        return str(self.Emp_ID)


# Orders Table
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

    Date = db.Column(db.String(50))
    Price = db.Column(db.Float)
    Discount = db.Column(db.Float)
    Status = db.Column(db.String(20), default="pending")  # pending / accepted / rejected

    # One order to many order items
    order_items = db.relationship(
        'OrderItem',
        backref=db.backref('order'),
        lazy=True
    )

    # newww Calculate total quantity from OrderItem
    @property
    def total_quantity(self):
        """Calculate total quantity from order items"""
        total = db.session.query(func.sum(OrderItem.Quantity))\
            .filter(OrderItem.Order_ID == self.Order_ID)\
            .scalar()
        return total or 0


# OrderItem Table (M–N link: Orders to Product)
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