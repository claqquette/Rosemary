from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from flask_login import login_user, logout_user, login_required, current_user
from .models import Employee, Customer
from . import db

auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')

        # Check if email ends with @rosemary.emp (employee)
        if email.endswith('@rosemary.emp'):
            employee = Employee.query.filter_by(Email=email).first()

            if employee:
                if employee.Password == password:
                    session['user_type'] = 'employee'
                    login_user(employee, remember=True)
                    return redirect(url_for('products'))
                else:
                    flash('Incorrect password', 'error')
            else:
                flash('Employee email does not exist.', 'error')

        # Otherwise treat as customer
        else:
            customer = Customer.query.filter_by(Email=email).first()

            if customer:
                if customer.Password == password:
                    session['user_type'] = 'customer'
                    login_user(customer, remember=True)
                    return redirect(url_for('shop'))
                else:
                    flash('Incorrect password', 'error')
            else:
                flash('Customer email does not exist.', 'error')

    return render_template("login.html", user=current_user)


@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == "POST":
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')

        # Prevent signup with employee email format
        if email.endswith('@rosemary.emp'):
            flash('Cannot create customer account with @rosemary.emp email. This is reserved for employees.', 'error')
            return render_template("signup.html", user=current_user)

        if len(name) < 3:
            flash('Name must be at least 3 characters.', 'error')
        elif len(password) < 3:
            flash('Password must be at least 3 characters.', 'error')
        elif len(phone) < 10:
            flash('Phone must be at least 10 characters.', 'error')
        else:
            email_exists = Customer.query.filter_by(Email=email).first()

            if email_exists:
                flash('Email already exists.', 'error')
            else:
                new_customer = Customer(
                    Name=name,
                    Email=email,
                    Phone_Num=phone,
                    Password=password
                )
                db.session.add(new_customer)
                db.session.commit()

                flash('Account created successfully!', 'success')
                return redirect(url_for('auth.login'))

    return render_template("signup.html", user=current_user)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect(url_for('landing'))