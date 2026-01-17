from flask import Blueprint, render_template, redirect, url_for, flash, session
from flask_login import login_required, current_user
from .models import Orders, OrderItem, Product, Customer, WarehouseItem
from . import db

employee_orders_bp = Blueprint("employee_orders", __name__)


def employee_only():
    return session.get("user_type") == "employee" and hasattr(current_user, "Emp_ID")


@employee_orders_bp.route("/employee/orders")
@login_required
def employee_orders():
    if not employee_only():
        return redirect(url_for("shop"))

    # pending orders + customer info
    pending_orders = (
        db.session.query(Orders, Customer)
        .join(Customer, Customer.Cust_ID == Orders.Cust_ID)
        .filter(Orders.Status == "pending")
        .order_by(Orders.Order_ID.desc())
        .all()
    )

    # build details: (order, customer, items)
    orders_details = []
    for order, customer in pending_orders:
        items = (
            db.session.query(OrderItem, Product)
            .join(Product, Product.Product_ID == OrderItem.Product_ID)
            .filter(OrderItem.Order_ID == order.Order_ID)
            .all()
        )
        orders_details.append((order, customer, items))

    return render_template("employee_orders.html", orders_details=orders_details)


@employee_orders_bp.route("/employee/orders/accept/<int:order_id>", methods=["POST"])
@login_required
def accept_order(order_id):
    if not employee_only():
        return redirect(url_for("shop"))

    order = Orders.query.get_or_404(order_id)

    if order.Status != "pending":
        flash("Order already handled.", "warning")
        return redirect(url_for("employee_orders.employee_orders"))

    order.Status = "accepted"
    order.Emp_ID = current_user.Emp_ID  # employee gets credit for sales
    db.session.commit()

    flash(f"Order {order.Order_ID} accepted.", "success")
    return redirect(url_for("employee_orders.employee_orders"))


@employee_orders_bp.route("/employee/orders/reject/<int:order_id>", methods=["POST"])
@login_required
def reject_order(order_id):
    if not employee_only():
        return redirect(url_for("shop"))

    order = Orders.query.get_or_404(order_id)

    if order.Status != "pending":
        flash("Order already handled.", "warning")
        return redirect(url_for("employee_orders.employee_orders"))

    # Restock warehouse items when rejected
    items = OrderItem.query.filter_by(Order_ID=order.Order_ID).all()

    for it in items:
        wi = WarehouseItem.query.filter_by(Product_ID=it.Product_ID).first()

        if not wi:
            wi = WarehouseItem(Product_ID=it.Product_ID, Quantity=0)
            db.session.add(wi)

        wi.Quantity = (wi.Quantity or 0) + (it.Quantity or 0)

    order.Status = "rejected"
    order.Emp_ID = None

    db.session.commit()

    flash(f"Order {order.Order_ID} rejected and stock restored.", "error")
    return redirect(url_for("employee_orders.employee_orders"))
