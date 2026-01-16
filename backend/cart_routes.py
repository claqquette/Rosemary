from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from flask_login import login_required, current_user, logout_user
from .models import Product, Orders, OrderItem, Customer
from . import db
from datetime import datetime

cart_bp = Blueprint('cart', __name__)


# Helper function to get cart from session
def get_cart():
    if 'cart' not in session:
        session['cart'] = {}
    return session['cart']


@cart_bp.route('/cart/add/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    # Check if user is logged in as customer BEFORE doing anything
    if not current_user.is_authenticated or session.get("user_type") != "customer":
        # Don't flash message, just redirect silently
        return redirect(url_for('auth.login'))

    product = Product.query.get_or_404(product_id)
    quantity = int(request.form.get('quantity', 1))

    # Check if enough stock
    if quantity > product.Quantity:
        flash(f'Only {product.Quantity} items available in stock.', 'error')
        return redirect(url_for('shop'))

    # Get cart from session
    cart = get_cart()

    # Add or update product in cart
    product_id_str = str(product_id)
    if product_id_str in cart:
        cart[product_id_str] += quantity
    else:
        cart[product_id_str] = quantity

    # Make sure total quantity doesn't exceed stock
    if cart[product_id_str] > product.Quantity:
        cart[product_id_str] = product.Quantity
        flash(f'Maximum quantity is {product.Quantity}', 'warning')

    session['cart'] = cart
    session.modified = True

    flash(f'{product.Name} added to cart!', 'success')
    return redirect(url_for('shop'))


@cart_bp.route('/cart')#-------updated
@login_required
def view_cart():
    if session.get("user_type") != "customer":
        return redirect(url_for('auth.login'))

    cart = get_cart()
    items = []
    total_before_discount = 0
    discount = 0

    for product_id, quantity in cart.items():
        product = Product.query.get(int(product_id))
        if product:
            items.append((product, quantity))
            total_before_discount += float(product.Price) * quantity
            discount += float(product.discount_amount) * quantity

    total_before_discount = round(total_before_discount, 2)
    discount = round(discount, 2)
    total = round(total_before_discount - discount, 2)

    return render_template(
        'cart.html',
        items=items,
        total=total,
        total_before_discount=total_before_discount,
        discount=discount
    )

#-------updated
@cart_bp.route('/cart/remove/<int:product_id>')
@login_required
def remove_from_cart(product_id):
    if session.get("user_type") != "customer":
        return redirect(url_for('auth.login'))

    cart = get_cart()
    product_id_str = str(product_id)

    if product_id_str in cart:
        del cart[product_id_str]
        session['cart'] = cart
        session.modified = True
        flash('Item removed from cart.', 'success')

    return redirect(url_for('cart.view_cart'))


@cart_bp.route('/checkout', methods=['GET', 'POST'])#------------------upadtated
@login_required
def checkout():
    # Check if user is a customer FIRST
    if session.get("user_type") != "customer":
        return redirect(url_for('auth.login'))

    # Also double-check that current_user has Cust_ID attribute
    if not hasattr(current_user, 'Cust_ID'):
        logout_user()
        session.clear()
        return redirect(url_for('auth.login'))

    cart = get_cart()

    if not cart:
        flash('Your cart is empty.', 'error')
        return redirect(url_for('shop'))

    # Calculate totals (GET part)
    items = []
    total_before_discount = 0
    discount = 0

    for product_id, quantity in cart.items():
        product = Product.query.get(int(product_id))
        if product:
            items.append((product, quantity))
            total_before_discount += float(product.Price) * quantity
            discount += float(product.discount_amount) * quantity

    total_before_discount = round(total_before_discount, 2)
    discount = round(discount, 2)
    total = round(total_before_discount - discount, 2)

    # POST part (when user confirms / submits checkout)
    if request.method == 'POST':
        final_price = total

        new_order = Orders(
            Cust_ID=current_user.Cust_ID,
            Date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            Price=final_price,
            Discount=discount,
            Quantity=sum(cart.values())
        )

        db.session.add(new_order)
        db.session.flush()

        # Add order items and update product quantities
        for product_id, quantity in cart.items():
            product = Product.query.get(int(product_id))
            if product:
                order_item = OrderItem(
                    Order_ID=new_order.Order_ID,
                    Product_ID=product.Product_ID,
                    Quantity=quantity
                )
                db.session.add(order_item)
                product.Quantity -= quantity

        db.session.commit()

        # Clear cart
        session['cart'] = {}
        session.modified = True

        flash(f'Order placed successfully! Order ID: {new_order.Order_ID}', 'success')
        return redirect(url_for('shop'))

    # GET view (show checkout page)
    return render_template(
        'checkout.html',
        items=items,
        total=total,
        discount=discount,
        total_before_discount=total_before_discount
    )
