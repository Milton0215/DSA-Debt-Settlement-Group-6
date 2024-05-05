# app/algorithm.py

def calculate_debts(group_name):
    '''
    Calculate debts within a group based on expenses. This function retrieves all expenses for the group and calculates
    how much each member owes or is owed, then simplifies these debts to minimize the number of transactions.

    Args:
        group_name (str): The name of the group.

    Returns:
        list: List of transactions indicating debts to be settled.
    '''
    from .models import Group  # Importing Group model locally to avoid circular dependency issues
    group = Group.query.filter_by(name=group_name).first()  # Query to find the group by name
    if not group:
        return []  # If the group doesn't exist, return an empty list

    expenses = group.expenses  # Retrieve all expenses linked to the group
    balances = {}  # Dictionary to store net balance of each member

    # Iterate through each expense to calculate the balance for each member
    for expense in expenses:
        if len(expense.debtors) > 0:  # Check if there are debtors for the expense
            amount_per_debtor = expense.amount / len(
                expense.debtors)  # Divide the expense amount by the number of debtors
            for debtor in expense.debtors:
                if debtor.id != expense.payer_id:  # Ensure debtor is not the payer
                    balances[debtor.id] = balances.get(debtor.id,
                                                       0) - amount_per_debtor  # Deduct amount from debtor's balance
                    balances[expense.payer_id] = balances.get(expense.payer_id,
                                                              0) + amount_per_debtor  # Add amount to payer's balance

    transactions = simplify_debts(balances)  # Call function to simplify the calculated balances into fewer transactions
    return transactions


def simplify_debts(balances):
    '''
    Simplify debts by minimizing the number of transactions needed to settle all balances. This function pairs debtors
    and creditors to settle debts directly.

    Args:
        balances (dict): A dictionary containing balances for each participant.

    Returns:
        list: List of simplified transactions indicating debts to be settled.
    '''
    balances_copy = balances.copy()  # Create a copy of balances to manipulate
    sorted_balances = sorted(balances_copy.items(), key=lambda x: x[1])  # Sort balances by amount
    debtors = 0
    creditors = len(sorted_balances) - 1
    transactions = []

    # Loop to create transactions between debtors and creditors
    while debtors <= creditors:
        debtor, debtor_balance = sorted_balances[debtors]
        creditor, creditor_balance = sorted_balances[creditors]

        # Skip transactions involving zero balances or self-debts
        if debtor_balance == 0 or debtor == creditor:
            debtors += 1
            continue
        if creditor_balance == 0 or debtor == creditor:
            creditors -= 1
            continue

        # Calculate the transfer amount
        transfer_amount = min(-debtor_balance, creditor_balance)
        debtor_balance += transfer_amount  # Adjust debtor's balance
        creditor_balance -= transfer_amount  # Adjust creditor's balance

        # Record the transaction if it's between different people and the amount is not zero
        if debtor != creditor and transfer_amount != 0:
            transactions.append({'debtor': debtor, 'creditor': creditor, 'amount': transfer_amount})

        # Update balances in the sorted list
        sorted_balances[debtors] = (debtor, debtor_balance)
        sorted_balances[creditors] = (creditor, creditor_balance)

        # Move to the next debtor or creditor as needed
        if debtor_balance == 0:
            debtors += 1
        if creditor_balance == 0:
            creditors -= 1

    return transactions