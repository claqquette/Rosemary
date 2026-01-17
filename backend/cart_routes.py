from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from flask_login import login_required, current_user, logout_user
from .models import Product, Orders, OrderItem, Employee, WarehouseItem
from . import db
from datetime import datetime

cart_bp = Blueprint('cart', __name__)


# ---------------------------
# Helper: get cart from session
# ---------------------------
def get_cart():
    if 'cart' not in session or not isinstance(session['cart'], dict):
        session['cart'] = {}
    return session['cart']


# ---------------------------
# Helper: Get or create default employee for online orders
# ---------------------------
def get_default_employee():
    """Get the default 'Online System' employee for customer self-checkout orders"""
    default_emp = Employee.query.filter_by(Email='system@rosemary.emp').first()

    if not default_emp:
        # Create default system employee if it doesn't exist
        default_emp = Employee(
            Name='Online System',
            Email='system@rosemary.emp',
            Password='system_only_no_login',  # Should use hashing in production
            Phone_Num='0000000000',
            Address='System'
        )
        db.session.add(default_emp)
        db.session.commit()

    return default_emp.Emp_ID


# ---------------------------
# Add to cart
# ---------------------------
@cart_bp.route('/cart/add/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    # Must be logged in as customer
    if not current_user.is_authenticated or session.get("user_type") != "customer":
        return redirect(url_for('auth.login'))

    product = Product.query.get_or_404(product_id)

    try:
        quantity = int(request.form.get('quantity', 1))
    except ValueError:
        quantity = 1

    if quantity < 1:
        quantity = 1

    # Check stock
    if quantity > product.stock_qty:
        flash(f'Only {product.stock_qty} items available in stock.', 'error')
        return redirect(url_for('shop'))

    cart = get_cart()
    pid = str(product_id)

    # Add/update
    cart[pid] = cart.get(pid, 0) + quantity

    # Don't exceed stock
    if cart[pid] > product.stock_qty:
        cart[pid] = product.stock_qty
        flash(f'Maximum quantity is {product.stock_qty}', 'warning')

    session['cart'] = cart
    session.modified = True

    flash(f'{product.Name} added to cart!', 'success')
    return redirect(url_for('shop'))


# ---------------------------
# View cart
# ---------------------------
@cart_bp.route('/cart')
@login_required
def view_cart():
    if session.get("user_type") != "customer":
        return redirect(url_for('auth.login'))

    cart = get_cart()

    items = []
    total_before_discount = 0.0
    discount_total = 0.0

    for product_id, qty in cart.items():
        product = Product.query.get(int(product_id))
        if not product:
            continue

        qty = int(qty)
        items.append((product, qty))

        price = float(product.Price or 0)
        total_before_discount += price * qty
        discount_total += float(product.discount_amount) * qty

    total_before_discount = round(total_before_discount, 2)
    discount_total = round(discount_total, 2)
    total = round(total_before_discount - discount_total, 2)

    return render_template(
        'cart.html',
        items=items,
        total_before_discount=total_before_discount,
        discount=discount_total,
        total=total
    )


# ---------------------------
# Remove item
# ---------------------------
@cart_bp.route('/cart/remove/<int:product_id>')
@login_required
def remove_from_cart(product_id):
    if session.get("user_type") != "customer":
        return redirect(url_for('auth.login'))

    cart = get_cart()
    pid = str(product_id)

    if pid in cart:
        del cart[pid]
        session['cart'] = cart
        session.modified = True
        flash('Item removed from cart.', 'success')

    return redirect(url_for('cart.view_cart'))


# ---------------------------
# Checkout: PLACE ORDER IMMEDIATELY
# (customer presses checkout button in cart)
# ---------------------------
@cart_bp.route('/checkout', methods=['POST'])
@login_required
def checkout():
    if session.get("user_type") != "customer":
        return redirect(url_for('auth.login'))

    # Must be a customer object
    if not hasattr(current_user, 'Cust_ID'):
        logout_user()
        session.clear()
        return redirect(url_for('auth.login'))

    cart = get_cart()
    if not cart:
        flash('Your cart is empty.', 'error')
        return redirect(url_for('cart.view_cart'))

    # Build order totals + validate stock again
    total_before_discount = 0.0
    discount_total = 0.0

    products_in_cart = []  # store (product, qty)
    for product_id, qty in cart.items():
        product = Product.query.get(int(product_id))
        if not product:
            continue

        qty = int(qty)
        if qty < 1:
            continue

        # stock check
        if qty > (product.stock_qty or 0):
            flash(f'Not enough stock for {product.Name}. Available: {product.stock_qty}', 'error')
            return redirect(url_for('cart.view_cart'))

        products_in_cart.append((product, qty))

        price = float(product.Price or 0)
        total_before_discount += price * qty
        discount_total += float(product.discount_amount) * qty

    if not products_in_cart:
        flash('Your cart is empty.', 'error')
        return redirect(url_for('cart.view_cart'))

    total_before_discount = round(total_before_discount, 2)
    discount_total = round(discount_total, 2)
    final_price = round(total_before_discount - discount_total, 2)

    # Assign default employee for online orders
    default_emp_id = get_default_employee()

    #  Quantity field (it will be calculated from OrderItem)
    new_order = Orders(
        Cust_ID=current_user.Cust_ID,
        Emp_ID=default_emp_id,
        Date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        Price=final_price,
        Discount=discount_total
    )

    db.session.add(new_order)
    db.session.flush()  # get new_order.Order_ID without committing yet

    # Insert order items + reduce stock
    for product, qty in products_in_cart:
        #  Quantity is stored HERE in OrderItem
        db.session.add(OrderItem(
            Order_ID=new_order.Order_ID,
            Product_ID=product.Product_ID,
            Quantity=qty
        ))
        wi = WarehouseItem.query.filter_by(Product_ID=product.Product_ID).first()
        if not wi or (wi.Quantity or 0) < qty:
            flash(f"Not enough stock for {product.Name}", "error")
            return redirect(url_for('cart.view_cart'))
        wi.Quantity -= qty

    db.session.commit()

    # Clear cart
    session['cart'] = {}
    session.modified = True

    flash(f'Order placed successfully! Order ID: {new_order.Order_ID}', 'success')
    return redirect(url_for('shop'))


# Optional: if someone visits /checkout in browser (GET), redirect to cart
@cart_bp.route('/checkout', methods=['GET'])
@login_required
def checkout_get():
    return redirect(url_for('cart.view_cart'))