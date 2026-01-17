from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from flask_login import login_required
from .models import Product, WarehouseItem
from . import db

product_bp = Blueprint('product', __name__)


@product_bp.route('/product/add', methods=['GET', 'POST'])
@login_required
def add_product():
    if session.get("user_type") != "employee":
        flash('Access denied. Employees only.', 'error')
        return redirect(url_for('shop'))
#get data from inputs
    if request.method == 'POST':
        name = request.form.get('name')
        price = request.form.get('price')
        barcode = request.form.get('barcode')
        quantity = int(request.form.get('quantity') or 0)
        discount = int(request.form.get("discount_percent", 0))
        man_id_raw = (request.form.get('man_id') or '').strip()
        man_id = int(man_id_raw) if man_id_raw else None
        image = (request.form.get('image') or '').strip()
        image = image if image else None

        # Create Product with ALL fields
        new_product = Product(
            Name=name,
            Price=float(price),
            Discount_Percent=discount,
            Barcode=barcode,
            Man_ID=man_id,
            Image=image
        )

        db.session.add(new_product)
        db.session.flush()

        # Create WarehouseItem (Quantity lives here)
        wi = WarehouseItem(Product_ID=new_product.Product_ID, Quantity=quantity)
        db.session.add(wi)

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
    product.Price = float(request.form.get('price') or 0)
    product.Barcode = request.form.get('barcode')
    product.Discount_Percent = int(request.form.get("discount_percent", 0))

    # Manufacturer ID (allow empty -> NULL)
    man_raw = (request.form.get("man_id") or "").strip()
    product.Man_ID = int(man_raw) if man_raw else None

    # Image (allow empty -> NULL)
    image_raw = (request.form.get("image") or "").strip()
    product.Image = image_raw if image_raw else None

    # Quantity goes to WarehouseItem (not Product)
    qty = int(request.form.get("quantity") or 0)
    wi = WarehouseItem.query.filter_by(Product_ID=product.Product_ID).first()
    if not wi:
        wi = WarehouseItem(Product_ID=product.Product_ID, Quantity=0)
        db.session.add(wi)
    wi.Quantity = qty

    try:
        db.session.commit()
        flash('Product updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Update failed: {e}", "error")

    return redirect(url_for('products'))


@product_bp.route('/product/delete/<int:product_id>')
@login_required
def delete_product(product_id):
    if session.get("user_type") != "employee":
        flash('Access denied. Employees only.', 'error')
        return redirect(url_for('shop'))

    product = Product.query.get_or_404(product_id)

    try:
        # 1) delete warehouse row first (prevents Product_ID -> NULL problem)
        wi = WarehouseItem.query.filter_by(Product_ID=product_id).first()
        if wi:
            db.session.delete(wi)
        db.session.delete(product)
        db.session.commit()
        flash('Product deleted successfully!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f"Delete failed: {e}", "error")

    return redirect(url_for('products'))