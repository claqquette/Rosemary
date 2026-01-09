from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from flask_login import login_required, current_user
from .models import Product
from . import db

product_bp = Blueprint('product', __name__)


@product_bp.route('/product/add', methods=['GET', 'POST'])
@login_required
def add_product():
    if session.get("user_type") != "employee":
        flash('Access denied. Employees only.', 'error')
        return redirect(url_for('shop'))

    if request.method == 'POST':
        name = request.form.get('name')
        price = request.form.get('price')
        barcode = request.form.get('barcode')
        quantity = request.form.get('quantity')
        discount = int(request.form.get("discount_percent", 0))  #NEWW

        new_product = Product(
            Name=name,
            Price=float(price),
            Discount_Percent=discount,  # NEWW
            Barcode=barcode,
            Quantity=int(quantity)
        )

        db.session.add(new_product)
        db.session.commit()

        flash('Product added successfully!', 'success')
        return redirect(url_for('products'))

    return render_template('add_product.html')


@product_bp.route('/product/update/<int:product_id>', methods=['POST'])
@login_required
def update_product(product_id):
    if session.get("user_type") != "employee":
        flash('Access denied. Employees only.', 'error')
        return redirect(url_for('shop'))

    product = Product.query.get_or_404(product_id)

    product.Name = request.form.get('name')
    product.Price = float(request.form.get('price'))
    product.Barcode = request.form.get('barcode')
    product.Quantity = int(request.form.get('quantity'))
    product.Discount_Percent = int(request.form.get("discount_percent", 0)) #newww

    db.session.commit()

    flash('Product updated successfully!', 'success')
    return redirect(url_for('products'))


@product_bp.route('/product/delete/<int:product_id>')
@login_required
def delete_product(product_id):
    if session.get("user_type") != "employee":
        flash('Access denied. Employees only.', 'error')
        return redirect(url_for('shop'))

    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()

    flash('Product deleted successfully!', 'success')
    return redirect(url_for('products'))