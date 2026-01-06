from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from flask_login import login_required, current_user
from sqlalchemy import func, desc, and_
from .models import Product, Customer, Employee, Orders, OrderItem, Manufacturer, WarehouseItem
from . import db
from datetime import datetime

queries_bp = Blueprint('queries', __name__)


@queries_bp.route('/analytics')
@login_required
def analytics():
    if session.get("user_type") != "employee":
        return redirect(url_for('shop'))

    try:
        # 1. Retrieve all product details including name, price, and barcode number
        all_products = (
            db.session.query(
                Product.Product_ID,
                Product.Name,
                Product.Price,
                Product.Barcode,
                Product.Quantity
            )
            .all()
        )
    except Exception as e:
        print(f"Error in query 1: {e}")
        all_products = []

    try:
        # 2. Retrieve all customer information stored in the database
        all_customers = (
            db.session.query(
                Customer.Cust_ID,
                Customer.Name,
                Customer.Email,
                Customer.Phone_Num
            )
            .all()
        )
    except Exception as e:
        print(f"Error in query 2: {e}")
        all_customers = []

    try:
        # 3. Retrieve all employees and their contact information
        all_employees = (
            db.session.query(
                Employee.Emp_ID,
                Employee.Name,
                Employee.Email,
                Employee.Phone_Num,
                Employee.Address
            )
            .all()
        )
    except Exception as e:
        print(f"Error in query 3: {e}")
        all_employees = []

    try:
        # 4. Retrieve all orders placed by a specific customer (example: customer_id = 1)
        customer_id = 1
        customer_orders = (
            db.session.query(
                Orders.Order_ID,
                Orders.Date,
                Orders.Price,
                Orders.Quantity,
                Orders.Discount
            )
            .filter(Orders.Cust_ID == customer_id)
            .all()
        )
    except Exception as e:
        print(f"Error in query 4: {e}")
        customer_orders = []

    try:
        # 5. Retrieve all orders handled by a specific employee (example: employee_id = 1)
        employee_id = 1
        employee_orders = (
            db.session.query(
                Orders.Order_ID,
                Orders.Date,
                Orders.Price,
                Orders.Quantity,
                Orders.Discount
            )
            .filter(Orders.Emp_ID == employee_id)
            .all()
        )
    except Exception as e:
        print(f"Error in query 5: {e}")
        employee_orders = []

    try:
        # 6. Retrieve the total number of orders placed by each customer
        orders_per_customer = (
            db.session.query(
                Customer.Cust_ID,
                Customer.Name,
                func.count(Orders.Order_ID).label('total_orders')
            )
            .join(Orders, Orders.Cust_ID == Customer.Cust_ID)
            .group_by(Customer.Cust_ID)
            .order_by(desc('total_orders'))
            .all()
        )
    except Exception as e:
        print(f"Error in query 6: {e}")
        orders_per_customer = []

    try:
        # 7. Retrieve the total value of all items currently stored in the warehouse
        total_warehouse_value = (
            db.session.query(
                func.sum(Product.Price * WarehouseItem.Quantity).label('total_value')
            )
            .join(WarehouseItem, WarehouseItem.Product_ID == Product.Product_ID)
            .scalar()
        )
    except Exception as e:
        print(f"Error in query 7: {e}")
        total_warehouse_value = 0

    try:
        # 8. Retrieve all products supplied by a specific manufacturer (example: manufacturer_id = 1)
        manufacturer_id = 1
        products_by_manufacturer = (
            db.session.query(
                Product.Product_ID,
                Product.Name,
                Product.Price,
                Product.Barcode
            )
            .filter(Product.Man_ID == manufacturer_id)
            .all()
        )
    except Exception as e:
        print(f"Error in query 8: {e}")
        products_by_manufacturer = []

    try:
        # 9. Retrieve the average selling price of all products in the supermarket
        average_price = (
            db.session.query(
                func.avg(Product.Price).label('avg_price')
            )
            .scalar()
        )
    except Exception as e:
        print(f"Error in query 9: {e}")
        average_price = 0

    try:
        # 10. Retrieve all orders that include a discount
        orders_with_discount = (
            db.session.query(
                Orders.Order_ID,
                Orders.Date,
                Orders.Price,
                Orders.Discount,
                Customer.Name
            )
            .join(Customer, Customer.Cust_ID == Orders.Cust_ID)
            .filter(Orders.Discount > 0)
            .all()
        )
    except Exception as e:
        print(f"Error in query 10: {e}")
        orders_with_discount = []

    try:
        # 11. Retrieve all products currently available in the warehouse
        available_products = (
            db.session.query(
                Product.Product_ID,
                Product.Name,
                Product.Price,
                WarehouseItem.Quantity
            )
            .join(WarehouseItem, WarehouseItem.Product_ID == Product.Product_ID)
            .filter(WarehouseItem.Quantity > 0)
            .all()
        )
    except Exception as e:
        print(f"Error in query 11: {e}")
        available_products = []

    try:
        # 12. Retrieve all products that are low in stock (below a certain quantity)
        low_stock_threshold = 10
        low_stock_products = (
            db.session.query(
                Product.Product_ID,
                Product.Name,
                Product.Price,
                Product.Quantity
            )
            .filter(Product.Quantity < low_stock_threshold)
            .all()
        )
    except Exception as e:
        print(f"Error in query 12: {e}")
        low_stock_products = []

    try:
        # 13. Retrieve the manufacturer details of a specific product (example: product_id = 1)
        product_id = 1
        product_manufacturer = (
            db.session.query(
                Manufacturer.Man_ID,
                Manufacturer.Name,
                Manufacturer.Address,
                Manufacturer.Email
            )
            .join(Product, Product.Man_ID == Manufacturer.Man_ID)
            .filter(Product.Product_ID == product_id)
            .first()
        )
    except Exception as e:
        print(f"Error in query 13: {e}")
        product_manufacturer = None

    try:
        # 14. Get the customer who spent the most money
        top_spending_customer = (
            db.session.query(
                Customer.Cust_ID,
                Customer.Name,
                Customer.Email,
                func.sum(Orders.Price).label('total_spent')
            )
            .join(Orders, Orders.Cust_ID == Customer.Cust_ID)
            .group_by(Customer.Cust_ID)
            .order_by(desc('total_spent'))
            .first()
        )
    except Exception as e:
        print(f"Error in query 14: {e}")
        top_spending_customer = None

    try:
        # 15. Retrieve the customer who placed the highest number of orders
        most_orders_customer = (
            db.session.query(
                Customer.Cust_ID,
                Customer.Name,
                Customer.Email,
                func.count(Orders.Order_ID).label('order_count')
            )
            .join(Orders, Orders.Cust_ID == Customer.Cust_ID)
            .group_by(Customer.Cust_ID)
            .order_by(desc('order_count'))
            .first()
        )
    except Exception as e:
        print(f"Error in query 15: {e}")
        most_orders_customer = None

    try:
        # 16. Get the most recent order made
        most_recent_order = (
            db.session.query(
                Orders.Order_ID,
                Orders.Date,
                Orders.Price,
                Customer.Name
            )
            .join(Customer, Customer.Cust_ID == Orders.Cust_ID)
            .order_by(desc(Orders.Date))
            .first()
        )
    except Exception as e:
        print(f"Error in query 16: {e}")
        most_recent_order = None

    try:
        # 17. Retrieve orders placed within a specific date range
        start_date = '2024-01-01'
        end_date = '2024-12-31'
        orders_in_date_range = (
            db.session.query(
                Orders.Order_ID,
                Orders.Date,
                Orders.Price,
                Customer.Name
            )
            .join(Customer, Customer.Cust_ID == Orders.Cust_ID)
            .filter(and_(Orders.Date >= start_date, Orders.Date <= end_date))
            .all()
        )
    except Exception as e:
        print(f"Error in query 17: {e}")
        orders_in_date_range = []

    try:
        # 18. Get the employee who sold the most products
        top_selling_employee = (
            db.session.query(
                Employee.Emp_ID,
                Employee.Name,
                Employee.Email,
                func.sum(OrderItem.Quantity).label('total_sold')
            )
            .join(Orders, Orders.Emp_ID == Employee.Emp_ID)
            .join(OrderItem, OrderItem.Order_ID == Orders.Order_ID)
            .group_by(Employee.Emp_ID)
            .order_by(desc('total_sold'))
            .first()
        )
    except Exception as e:
        print(f"Error in query 18: {e}")
        top_selling_employee = None

    try:
        # 19. Retrieve all products along with their corresponding manufacturer names
        products_with_manufacturers = (
            db.session.query(
                Product.Product_ID,
                Product.Name,
                Product.Price,
                Manufacturer.Name.label('manufacturer_name')
            )
            .outerjoin(Manufacturer, Manufacturer.Man_ID == Product.Man_ID)
            .all()
        )
    except Exception as e:
        print(f"Error in query 19: {e}")
        products_with_manufacturers = []

    try:
        # 20. Get total sales for each month (MySQL version)
        monthly_sales = (
            db.session.query(
                func.date_format(Orders.Date, '%Y-%m').label('month'),
                func.sum(Orders.Price).label('total_sales'),
                func.count(Orders.Order_ID).label('order_count')
            )
            .group_by(func.date_format(Orders.Date, '%Y-%m'))
            .order_by('month')
            .all()
        )
    except Exception as e:
        print(f"Error in query 20: {e}")
        monthly_sales = []

    # Already implemented in other parts:
    # - Login functionality (auth.py)
    # - Add/Update/Delete products (product_routes.py)
    # - View cart (cart_routes.py)
    # - Checkout process (cart_routes.py)

    return render_template('analytics.html',
                           all_products=all_products,
                           all_customers=all_customers,
                           all_employees=all_employees,
                           customer_orders=customer_orders,
                           employee_orders=employee_orders,
                           orders_per_customer=orders_per_customer,
                           total_warehouse_value=total_warehouse_value,
                           products_by_manufacturer=products_by_manufacturer,
                           average_price=average_price,
                           orders_with_discount=orders_with_discount,
                           available_products=available_products,
                           low_stock_products=low_stock_products,
                           product_manufacturer=product_manufacturer,
                           top_spending_customer=top_spending_customer,
                           most_orders_customer=most_orders_customer,
                           most_recent_order=most_recent_order,
                           orders_in_date_range=orders_in_date_range,
                           top_selling_employee=top_selling_employee,
                           products_with_manufacturers=products_with_manufacturers,
                           monthly_sales=monthly_sales)