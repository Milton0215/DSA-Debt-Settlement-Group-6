from . import db  # Import db from the local package init
from flask_login import UserMixin

class User(db.Model, UserMixin):
    """
    Model representing a user.

    Attributes:
        id (int): The unique identifier for the user.
        first_name (str): The first name of the user.
        last_name (str): The last name of the user.
        username (str): The username of the user (unique).
        password (str): The password of the user.
        paypal_username (str): The PayPal username of the user (unique).
        groups (relationship): Relationship with Group model representing the groups the user belongs to.
        expenses_paid (relationship): Relationship with Expense model representing the expenses paid by the user.
    """
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    paypal_username = db.Column(db.String(80), unique=True, nullable=False)
    groups = db.relationship('Group', secondary='user_group', backref='members')
    expenses_paid = db.relationship('Expense', backref='payer', foreign_keys='Expense.payer_id')

class Group(db.Model):
    """
    Model representing a group.

    Attributes:
        id (int): The unique identifier for the group.
        name (str): The name of the group.
        expenses (relationship): Relationship with Expense model representing the expenses of the group.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    expenses = db.relationship('Expense', backref='group')

class UserGroup(db.Model):
    """
    Association table representing the relationship between users and groups.

    Attributes:
        user_id (int): The ID of the user.
        group_id (int): The ID of the group.
    """
    __tablename__ = 'user_group'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), primary_key=True)


class Expense(db.Model):
    """
    Model representing an expense.

    Attributes:
        id (int): The unique identifier for the expense.
        description (str): The description of the expense.
        amount (float): The amount of the expense.
        payer_id (int): The ID of the user who paid the expense.
        group_id (int): The ID of the group associated with the expense.
        debtors (relationship): Relationship with User model representing the users who owe the expense.
        settled (bool): Flag indicating if the expense has been settled.
    """
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    debtors = db.relationship('User', secondary='expense_debtors', backref=db.backref('debts'))
    settled = db.Column(db.Boolean, default=False, nullable=False)


class ExpenseDebtor(db.Model):
    """
    Association table representing the relationship between expenses and debtors.

    Attributes:
        expense_id (int): The ID of the expense.
        debtor_id (int): The ID of the debtor.
    """
    __tablename__ = 'expense_debtors'
    expense_id = db.Column(db.Integer, db.ForeignKey('expense.id'), primary_key=True)
    debtor_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
