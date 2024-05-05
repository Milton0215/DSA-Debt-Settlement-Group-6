# app/routes.py
from flask import render_template, request, redirect, url_for, flash, abort, session, get_flashed_messages
from .models import User, Group, UserGroup, Expense, db # Import the models
from flask_login import login_required, current_user, login_user, logout_user
from .algorithm import calculate_debts

def init_routes(app):
    @app.route('/')
    def home():
        return render_template('home.html')

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            # Get user input data
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            username = request.form['username']
            password = request.form['password']
            paypal_username = request.form['paypal_username']

            # Check if username already exists
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                flash('Username already taken or account already exists. Please try to log in.', 'warning')
                return redirect(url_for('register'))  # Redirect to register page with warning message

            # Create new user
            new_user = User(first_name=first_name, last_name=last_name, username=username, password=password,
                            paypal_username=paypal_username)
            db.session.add(new_user)
            db.session.commit()
            flash('User registered successfully. Please log in.', 'success')
            return redirect(url_for('login'))  # Redirect to login after successful registration

        return render_template('register.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))  # Redirect if already logged in
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']  # Get password from the form
            user = User.query.filter_by(username=username).first()
            if user and user.password == password:  # Directly compare passwords
                flash('Login successful!', 'success')  # Flash success message
                login_user(user)
                return redirect(url_for('dashboard'))  # Redirect to the dashboard after successful login
            else:
                flash('Invalid username or password', 'error')  # Flash error message
        return render_template('login.html')

    @app.route('/dashboard')
    @login_required
    def dashboard():
        """
        Route to display the user dashboard including all groups the user is a member of,
        option to create a new group and join an existing group.
        """
        user_groups = current_user.groups  # Get all groups of the current user
        return render_template('dashboard.html', user_groups=user_groups)

    @app.route('/create_group', methods=['GET', 'POST'])
    @login_required
    def create_group():
        """
        Route to create a new group.

        If the request method is POST, it creates a new group with the given name
        and adds the current user as a member.

        Returns:
            Redirect: Redirects to the dashboard after creating the group.
            Rendered Template: Renders the 'create_group.html' template for GET requests.
        """
        if request.method == 'POST':
            group_name = request.form['group_name']
            new_group = Group(name=group_name)
            new_group.members.append(current_user)  # Add creator as a member
            db.session.add(new_group)
            db.session.commit()
            flash('New group created!', 'success')
            return redirect(url_for('dashboard'))
        return render_template('create_group.html')

    @app.route('/join_group', methods=['GET', 'POST'])
    @login_required
    def join_group():
        """
        Route to join an existing group.

        If the request method is POST, it adds the current user to the group if found.

        Returns:
            Redirect: Redirects to the dashboard after joining the group.
            Rendered Template: Renders the 'join_group.html' template for GET requests.
        """
        if request.method == 'POST':
            group_name = request.form['group_name']
            group = Group.query.filter_by(name=group_name).first()
            if group:
                current_user.groups.append(group)
                db.session.commit()
                flash('Joined group successfully!', 'success')
            else:
                flash('Group not found!', 'error')
            return redirect(url_for('dashboard'))
        return render_template('join_group.html')

    @app.route('/group_intermediate/<group_name>', methods=['GET'])
    @login_required
    def group_intermediate(group_name):
        """
        Route to display an intermediate page before entering a group.

        Args:
            group_name (str): The name of the group.

        Returns:
            Rendered Template: Renders the 'group_intermediate.html' template with group information.
        """
        group = Group.query.filter_by(name=group_name).first()
        if not group:
            abort(404)  # Group not found, return 404 error
        return render_template('group_intermediate.html', group=group, group_name=group.name)

    @app.route('/add_expense/<group_name>', methods=['GET', 'POST'])
    @login_required
    def add_expense(group_name):
        """
        Route to add an expense to a group.

        Args:
            group_name (str): The name of the group.

        Returns:
            Redirect: Redirects to the group dashboard after adding the expense.
            Rendered Template: Renders the 'add_expense.html' template with group and participant information.
        """
        group = Group.query.filter_by(name=group_name).first()
        if not group:
            flash("Group not found.", "error")
            return redirect(url_for('dashboard'))

        participants = group.members

        if request.method == 'POST':
            payer_id = request.form['payer_id']
            description = request.form['description']
            amount = request.form['amount']

            # Validate the amount to ensure it's a positive integer
            try:
                amount = float(amount)  # Convert input to float first to handle inputs like "100.00"
                if amount <= 0:
                    raise ValueError("The amount must be positive.")
            except ValueError as e:
                flash(f"Invalid amount: {str(e)}", 'error')
                return render_template('add_expense.html', group=group, participants=participants,
                                       group_name=group_name)

            # Get list of selected debtors
            selected_debtors = request.form.getlist('debtors')

            new_expense = Expense(payer_id=payer_id, group_id=group_name, description=description, amount=amount)
            db.session.add(new_expense)

            # Add selected debtors to the expense
            for debtor_id in selected_debtors:
                debtor = User.query.get(debtor_id)
                new_expense.debtors.append(debtor)

            db.session.commit()

            flash('Expense added successfully!', 'success')
            return redirect(url_for('group_dashboard', group_name=group.name))

        return render_template('add_expense.html', group=group, participants=participants)

    '''
    @app.route('/group_summary/<int:group_id>', methods=['GET'])
    @login_required
    def group_summary(group_id):
        """
        Route to display a summary of expenses for a group.
        """
        group = Group.query.get(group_id)
        if not group:
            flash("Group not found.", "error")
            return redirect(url_for('dashboard'))  # Or another appropriate fallback route
        group_name = group.name
        expenses = Expense.query.filter_by(group_id=group_id).all()  # Fetch expenses for the group

        return render_template('group_dashboard.html', group=group,
                               group_name=group_name, expenses=expenses, group_id=group_id)
                               
    '''

    @app.route('/group_dashboard/<group_name>', methods=['GET'])
    @login_required
    def group_dashboard(group_name):
        """
        Route to display the dashboard/summary of all expenses for a group.
        """
        group = Group.query.filter_by(name=group_name).first_or_404()

        expenses = Expense.query.filter_by(group_id=group.id).all()

        # Calculate the total spent
        total_spent = sum(expense.amount for expense in expenses)

        # Prepare past expenses with the current user displayed as "You"
        past_expenses = [
            {
                'spender': "You" if expense.payer_id == current_user.id else User.query.get(
                    expense.payer_id).first_name,
                'amount': expense.amount,
                'description': expense.description
            } for expense in expenses
        ]

        # Prepare nodes and edges for the debt graph
        nodes = set()
        edges = []
        for expense in expenses:
            nodes.add(expense.payer_id)  # Ensure payer is added as a node
            split_amount = expense.amount / max(len(expense.debtors), 1)  # Safely handle division
            for debtor in expense.debtors:
                if debtor.id != expense.payer_id:
                    nodes.add(debtor.id)
                    edges.append({
                        'from': expense.payer_id,
                        'to': debtor.id,
                        'label': f"€{split_amount:.2f}"
                    })

        # Map node IDs to user first names
        nodes = [{'id': node_id, 'label': User.query.get(node_id).first_name} for node_id in nodes]

        return render_template('group_dashboard.html', group=group, total_spent=total_spent,
                               past_expenses=past_expenses, nodes=nodes, edges=edges, group_name=group_name)

    @app.route('/settle_debts/<group_name>', methods=['GET'])
    @login_required
    def settle_debts(group_name):
        """
        Route to display debts for a group and allow users to settle them.
        Includes personalized messages for each transaction and PayPal button.
        """
        group = Group.query.filter_by(name=group_name).first()
        if not group:
            flash("Group not found.", "error")
            return redirect(url_for('dashboard'))

        transactions = calculate_debts(group_name)

        # Enrich transactions with names and PayPal usernames
        for transaction in transactions:
            debtor = User.query.get(transaction['debtor'])
            creditor = User.query.get(transaction['creditor'])

            # Check if the debtor or creditor is the current user
            transaction['debtor_name'] = "You" if debtor.id == current_user.id else debtor.first_name
            transaction['creditor_name'] = "You" if creditor.id == current_user.id else creditor.first_name

            transaction['creditor_paypal_username'] = creditor.paypal_username
            transaction['amount'] = "{:.2f}€".format(transaction['amount'])

            # Prepare a message for display in the template
            transaction['message'] = create_personalized_message(transaction, debtor, creditor)

        # Important: Sort transactions to show current user's debts first
        sorted_transactions = sorted(transactions, key=lambda t: t['debtor'] == current_user.id, reverse=True)

        return render_template('settle_debts.html', group=group, transactions=sorted_transactions, group_name=group_name)

    def create_personalized_message(transaction, debtor, creditor):
        """
        Create a personalized message for the transaction.
        """
        if debtor.id == current_user.id:
            return f"You owe {transaction['creditor_name']} {transaction['amount']}"
        elif creditor.id == current_user.id:
            return f"{transaction['debtor_name']} owes you {transaction['amount']}"
        else:
            return f"{transaction['debtor_name']} owes {transaction['creditor_name']} {transaction['amount']}"


    @app.route('/debt_graph/<int:group_id>', methods=['GET'])
    @login_required
    def debt_graph(group_id):
        """
        Route to display a debt graph for a group.
        """
        group = Group.query.get_or_404(group_id)
        nodes = set()
        edges = []

        expenses = Expense.query.filter_by(group_id=group_id).all()
        for expense in expenses:
            nodes.add(expense.payer_id)  # Ensure payer is added as a node
            if len(expense.debtors) > 0:  # Check to avoid division by zero
                split_amount = expense.amount / len(expense.debtors)  # Divide expense by number of debtors
                for debtor in expense.debtors:
                    if debtor.id != expense.payer_id:
                        nodes.add(debtor.id)
                        edges.append({
                            'from': expense.payer_id,
                            'to': debtor.id,
                            'label': f"€{split_amount:.2f}"
                        })
            else:
                # Handle the case where there are no debtors
                # You could add a self-loop or simply ignore this case
                print("Expense with ID", expense.id, "has no debtors.")

        # Map node IDs to user first names
        nodes = [{'id': node_id, 'label': User.query.get(node_id).first_name} for node_id in nodes]

        return render_template('debt_graph.html', nodes=nodes, edges=edges, group=group)

    @app.route('/logout', methods=['POST'])
    @login_required
    def logout():
        """
        Route to logout the current user.
        Automatically logs out users once app is closed.
        """
        logout_user()
        return redirect(url_for('home'))  # Redirect to home after logout



