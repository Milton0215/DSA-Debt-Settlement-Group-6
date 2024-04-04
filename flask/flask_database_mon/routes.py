from flask import render_template, request, redirect, url_for, flash
from .flask_app import app, db
from .flask_app import User, Expense

# Routes
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/add_user', methods=['POST'])
def add_user():
    real_name = request.form['name']
    paypal_username = request.form['paypalUsername']

    existing_user = User.query.filter_by(real_name=real_name).first()
    if existing_user:
        flash('User already exists!', 'danger')
        return redirect(url_for('enter_costs'))

    new_user = User(real_name=real_name, paypal_username=paypal_username)
    db.session.add(new_user)
    db.session.commit()

    flash('User added successfully!', 'success')
    return redirect(url_for('enter_costs'))

@app.route('/enter_costs')
def enter_costs():
    users = User.query.all()
    return render_template('enter_costs.html', users=users)

@app.route('/submit_cost', methods=['POST'])
def submit_cost():
    user_id = request.form['user_id']
    description = request.form['description']
    amount = float(request.form['amount'])
    expense = Expense(user_id=user_id, description=description, amount=amount)
    db.session.add(expense)
    db.session.commit()
    flash('Expense submitted successfully!', 'success')
    return redirect(url_for('summary'))

@app.route('/summary')
def summary():
    expenses = Expense.query.all()
    users = User.query.all()
    balances = calculate_balances(expenses, users)
    transactions = settle_debts(balances)
    transactions_with_links = calculate_and_link_settlements(transactions, users)
    total = sum(expense.amount for expense in expenses)
    return render_template('summary.html', total=total, expenses=expenses, balances=balances, transactions_with_links=transactions_with_links, users=users)
