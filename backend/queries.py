from flask import Blueprint, render_template, request, redirect, url_for, session
from flask_login import login_required
from sqlalchemy import func, desc
from sqlalchemy import case
from .models import Product, Customer, Employee, Orders, OrderItem, Manufacturer, WarehouseItem
from . import db

queries_bp = Blueprint('queries', __name__)

@queries_bp.route('/analytics')
@login_required
def analytics():
    if session.get("user_type") != "employee":
        return redirect(url_for('shop'))

    # Dynamic inputs
    customer_id = request.args.get("customer_id", type=int)                 # Query 4
    employee_id = request.args.get("employee_id", type=int)                 # Query 5 (optional)
    manufacturer_id = request.args.get("manufacturer_id", type=int)         # Query 8
    low_stock_threshold = request.args.get("low_stock", default=10, type=int)  # Query 12
    product_id = request.args.get("product_id", type=int)                   # Query 13
    start_date = request.args.get("start_date")                             # Query 17
    end_date = request.args.get("end_date")                                 # Query 17

    # 1) All products
    try:
        all_products = (
            db.session.query(
                Product.Product_ID,
                Product.Name,
                Product.Price,
                Product.Barcode,
                func.coalesce(WarehouseItem.Quantity, 0).label("Quantity")
            )
            .outerjoin(WarehouseItem, WarehouseItem.Product_ID == Product.Product_ID)
            .order_by(Product.Product_ID.asc())
            .all()
        )
    except Exception as e:
        print(f"Error in query 1: {e}")
        all_products = []

    # 2) All customers
    try:
        all_customers = (
            db.session.query(
                Customer.Cust_ID,
                Customer.Name,
                Customer.Email,
                Customer.Phone_Num
            )
            .order_by(Customer.Cust_ID.asc())
            .all()
        )
    except Exception as e:
        print(f"Error in query 2: {e}")
        all_customers = []

    # 3) All employees
    try:
        all_employees = (
            db.session.query(
                Employee.Emp_ID,
                Employee.Name,
                Employee.Email,
                Employee.Phone_Num,
                Employee.Address
            )
            .order_by(Employee.Emp_ID.asc())
            .all()
        )
    except Exception as e:
        print(f"Error in query 3: {e}")
        all_employees = []

    # 4) Orders by customer (dynamic)

    try:
        if customer_id:
            customer_orders = (
                db.session.query(Orders)
                .filter(Orders.Cust_ID == customer_id)
                .order_by(Orders.Order_ID.desc())
                .all()
            )
        else:
            customer_orders = []
    except Exception as e:
        print(f"Error in query 4: {e}")
        customer_orders = []

    # 5) Orders by employee (dynamic)
    try:
        if employee_id:
            employee_orders = (
                db.session.query(Orders)
                .filter(Orders.Emp_ID == employee_id)
                .order_by(Orders.Order_ID.desc())
                .all()
            )
        else:
            employee_orders = []
    except Exception as e:
        print(f"Error in query 5: {e}")
        employee_orders = []

    # 6) Total orders per customer
    try:
        orders_per_customer = (
            db.session.query(
                Customer.Cust_ID,
                Customer.Name,
                func.count(Orders.Order_ID).label('total_orders')
            )
            .join(Orders, Orders.Cust_ID == Customer.Cust_ID)
            .group_by(Customer.Cust_ID, Customer.Name)
            .order_by(desc('total_orders'))
            .all()
        )
    except Exception as e:
        print(f"Error in query 6: {e}")
        orders_per_customer = []

    # 7) Total warehouse value
    try:
        total_warehouse_value = (
            db.session.query(
                func.sum(Product.Price * WarehouseItem.Quantity).label('total_value')
            )
            .join(WarehouseItem, WarehouseItem.Product_ID == Product.Product_ID)
            .scalar()
        ) or 0
    except Exception as e:
        print(f"Error in query 7: {e}")
        total_warehouse_value = 0

    # 8) Products by manufacturer (dynamic)

    try:
        if manufacturer_id:
            products_by_manufacturer = (
                db.session.query(
                    Product.Product_ID,
                    Product.Name,
                    Product.Price,
                    Product.Barcode
                )
                .filter(Product.Man_ID == manufacturer_id)
                .order_by(Product.Product_ID.asc())
                .all()
            )
        else:
            products_by_manufacturer = []
    except Exception as e:
        print(f"Error in query 8: {e}")
        products_by_manufacturer = []

    # 9) Average product price

    try:
        average_price = db.session.query(func.avg(Product.Price)).scalar() or 0
    except Exception as e:
        print(f"Error in query 9: {e}")
        average_price = 0


    # 10) Customers who ONLY buy discounted orders, (they have no order with net discount=0)
    try:
        discount_only_customers = (
            db.session.query(
                Customer.Cust_ID,
                Customer.Name,
                Customer.Email,
                func.count(Orders.Order_ID).label("total_orders"),
                func.min(Orders.Discount).label("min_discount")
            )
            .join(Orders, Orders.Cust_ID == Customer.Cust_ID)
            .filter(Orders.Status == "accepted")
            .group_by(Customer.Cust_ID, Customer.Name, Customer.Email)
            .having(func.min(Orders.Discount) > 0)
            .order_by(desc("total_orders"))
            .all()
        )

    except Exception as e:
        print(f"Error in query 10: {e}")
        discount_only_customers = []

    # 11) Available products in warehouse
    try:
        available_products = (
            db.session.query(
                Product.Product_ID,
                Product.Name,
                Product.Price,
                func.coalesce(WarehouseItem.Quantity, 0).label("Quantity")
            )
            .join(WarehouseItem, WarehouseItem.Product_ID == Product.Product_ID)
            .filter(WarehouseItem.Quantity > 0)
            .order_by(WarehouseItem.Quantity.desc())
            .all()
        )
    except Exception as e:
        print(f"Error in query 11: {e}")
        available_products = []

    # 12) Low stock products (dynamic threshold)
    try:
        low_stock_products = (
            db.session.query(
                Product.Product_ID,
                Product.Name,
                Product.Price,
                func.coalesce(WarehouseItem.Quantity, 0).label("Quantity")
            )
            .outerjoin(WarehouseItem, WarehouseItem.Product_ID == Product.Product_ID)
            .filter(func.coalesce(WarehouseItem.Quantity, 0) < low_stock_threshold)
            .order_by(func.coalesce(WarehouseItem.Quantity, 0).asc())
            .all()
        )
    except Exception as e:
        print(f"Error in query 12: {e}")
        low_stock_products = []

    # 13) Manufacturer of a product (dynamic product_id)
    try:
        if product_id:
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
        else:
            product_manufacturer = None
    except Exception as e:
        print(f"Error in query 13: {e}")
        product_manufacturer = None

    # 14) Top spending customer
    try:
        top_spending_customer = (
            db.session.query(
                Customer.Cust_ID,
                Customer.Name,
                Customer.Email,
                func.sum(Orders.Price).label('total_spent')
            )
            .join(Orders, Orders.Cust_ID == Customer.Cust_ID)
            .group_by(Customer.Cust_ID, Customer.Name, Customer.Email)
            .order_by(desc('total_spent'))
            .first()
        )
    except Exception as e:
        print(f"Error in query 14: {e}")
        top_spending_customer = None

    # 15) Customer with most orders
    try:
        most_orders_customer = (
            db.session.query(
                Customer.Cust_ID,
                Customer.Name,
                Customer.Email,
                func.count(Orders.Order_ID).label('order_count')
            )
            .join(Orders, Orders.Cust_ID == Customer.Cust_ID)
            .group_by(Customer.Cust_ID, Customer.Name, Customer.Email)
            .order_by(desc('order_count'))
            .first()
        )
    except Exception as e:
        print(f"Error in query 15: {e}")
        most_orders_customer = None

    # 16) Most recent order
    try:
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

    # 17) Orders in date range (dynamic)
    try:
        if start_date and end_date:
            orders_in_date_range = (
                db.session.query(
                    Orders.Order_ID,
                    Orders.Date,
                    Orders.Price,
                    Orders.Status,
                    Customer.Name.label("customer_name")
                )
                .join(Customer, Customer.Cust_ID == Orders.Cust_ID)
                .filter(Orders.Date >= start_date, Orders.Date <= end_date)
                .order_by(Orders.Date.desc())
                .all()
            )
        else:
            orders_in_date_range = []
    except Exception as e:
        print(f"Error in query 17: {e}")
        orders_in_date_range = []

    # 18) Top selling employee (accepted orders only)
    try:
        top_selling_employee = (
            db.session.query(
                Employee.Name.label("Name"),
                Employee.Email.label("Email"),
                func.sum(OrderItem.Quantity).label("total_sold")
            )
            .join(Orders, Orders.Emp_ID == Employee.Emp_ID)
            .join(OrderItem, OrderItem.Order_ID == Orders.Order_ID)
            .filter(func.lower(Orders.Status) == 'accepted')
            .filter(Orders.Emp_ID.isnot(None))
            .group_by(Employee.Emp_ID, Employee.Name, Employee.Email)
            .order_by(desc("total_sold"))
            .first()
        )
    except Exception as e:
        print(f"Error in query 18: {e}")
        top_selling_employee = None

    # 19) Products with manufacturer names
    try:
        products_with_manufacturers = (
            db.session.query(
                Product.Product_ID,
                Product.Name,
                Product.Price,
                Manufacturer.Name.label('manufacturer_name')
            )
            .outerjoin(Manufacturer, Manufacturer.Man_ID == Product.Man_ID)
            .order_by(Product.Product_ID.asc())
            .all()
        )
    except Exception as e:
        print(f"Error in query 19: {e}")
        products_with_manufacturers = []

    # 20. Customers who spent more than average

    # First: total spent per customer
    subquery = (
        db.session.query(
            Orders.Cust_ID,
            func.sum(Orders.Price).label("total_spent")
        )
        .group_by(Orders.Cust_ID)
        .subquery()
    )

    # Second: average of total spent
    avg_spent = db.session.query(func.avg(subquery.c.total_spent)).scalar()
    if avg_spent is None:
        customers_above_avg = []#so the site dont crash when theeres no orders
    # Final: customers above average
    customers_above_avg = (
        db.session.query(Customer, subquery.c.total_spent)
        .join(subquery, Customer.Cust_ID == subquery.c.Cust_ID)
        .filter(subquery.c.total_spent > avg_spent)
        .order_by(subquery.c.total_spent.desc())
        .all()
    )

    return render_template(
        'analytics.html',
        # results
        all_products=all_products,
        all_customers=all_customers,
        all_employees=all_employees,
        customer_orders=customer_orders,
        employee_orders=employee_orders,
        orders_per_customer=orders_per_customer,
        total_warehouse_value=total_warehouse_value,
        products_by_manufacturer=products_by_manufacturer,
        average_price=average_price,
        discount_only_customers=discount_only_customers,
        available_products=available_products,
        low_stock_products=low_stock_products,
        product_manufacturer=product_manufacturer,
        top_spending_customer=top_spending_customer,
        most_orders_customer=most_orders_customer,
        most_recent_order=most_recent_order,
        orders_in_date_range=orders_in_date_range,
        top_selling_employee=top_selling_employee,
        products_with_manufacturers=products_with_manufacturers,
        customers_above_avg=customers_above_avg,
        # keep input values
        customer_id=customer_id,
        employee_id=employee_id,
        manufacturer_id=manufacturer_id,
        low_stock_threshold=low_stock_threshold,
        product_id=product_id,
        start_date=start_date,
        end_date=end_date
    )