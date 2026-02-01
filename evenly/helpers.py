import requests
import re
import random
import string
from datetime import datetime

from flask import redirect, render_template, session, request, url_for
from functools import wraps
from database import get_db_connection

def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/latest/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("start.html")
        return f(*args, **kwargs)

    return decorated_function

def apology(message, code=400):
    """
    Store the error message in the session and redirect.
    """
    session["error"] = message  # Store the error
    return redirect(request.referrer or "/start")


def settle_algorithm(group_id):
    print(f"Running settle_algorithm for group {group_id}")
    conn = get_db_connection()
    cursor = conn.cursor()

    # Step 1: Clear only UNPAID settlements
    cursor.execute("""
        DELETE FROM Settlements
        WHERE group_id = ?
        AND status = 'unpaid'
    """, (group_id,))

    # Step 2: Fetch all users in the group
    cursor.execute("SELECT user_id FROM GroupMembers WHERE group_id = ?", (group_id,))
    all_users = [row[0] for row in cursor.fetchall()]

    # Step 3: Initialize balances for all users
    balances = {user: 0.0 for user in all_users}

    # Step 4: Fetch individual debts from PaymentShares
    cursor.execute("""
        SELECT p.paid_by, ps.user_id, ps.share
        FROM PaymentShares ps
        JOIN Payments p ON ps.payment_id = p.payment_id
        WHERE p.group_id = ?
    """, (group_id,))
    payment_shares = cursor.fetchall()

    # Step 5: Update balances from PaymentShares
    for paid_by, user_id, share in payment_shares:
        if paid_by != user_id:  # Skip self-payments
            balances[user_id] -= share  # Debtor owes the share
            balances[paid_by] += share  # Creditor is owed the share

    # Step 6: Adjust balances with PAID settlements
    cursor.execute("""
        SELECT from_user, to_user, amount
        FROM Settlements
        WHERE group_id = ?
        AND status = 'paid'
    """, (group_id,))
    paid_settlements = cursor.fetchall()

    for from_user, to_user, amount in paid_settlements:
        balances[from_user] += amount  # Reduce debtor's debt
        balances[to_user] -= amount    # Reduce creditor's credit

    # Step 7: Identify debtors and creditors (rounded to avoid floating-point errors)
    creditors = sorted([(u, round(b, 2)) for u, b in balances.items() if b > 0], key=lambda x: x[1])
    debtors = sorted([(u, round(abs(b), 2)) for u, b in balances.items() if b < 0], key=lambda x: x[1])

    # Step 8: Calculate new settlements
    settlements = []
    i, j = 0, 0
    while i < len(debtors) and j < len(creditors):
        debtor, debt_amount = debtors[i]
        creditor, credit_amount = creditors[j]

        amount_to_transfer = min(debt_amount, credit_amount)
        settlements.append((debtor, creditor, amount_to_transfer))

        cursor.execute("""
            INSERT INTO Settlements (group_id, from_user, to_user, amount, status)
            VALUES (?, ?, ?, ?, ?)
        """, (group_id, debtor, creditor, amount_to_transfer, 'unpaid'))

        # Update remaining debts/credits
        debtors[i] = (debtor, debt_amount - amount_to_transfer)
        creditors[j] = (creditor, credit_amount - amount_to_transfer)

        if debtors[i][1] <= 0:
            i += 1
        if creditors[j][1] <= 0:
            j += 1

        print(f"Settling: {debtor} pays {creditor} ${amount_to_transfer:.2f}")

    conn.commit()
    conn.close()
    return settlements


def validate_form_input(form_data):

    for field, value in form_data.items():
        # Check if the field is empty
        if not value.strip():
            return f"{field.capitalize()} cannot be empty."

        # Check for harmful characters
        if re.search(r"[<>\"';]", value):
            return f"{field.capitalize()} contains invalid characters."

    return None

def validate_password(password):

    if len(password) < 7:
        return "Password must be at least 7 characters long."
    if not any(char.isupper() for char in password):
        return "Password must contain at least one uppercase letter."
    if not any(char.isdigit() for char in password):
        return "Password must contain at least one number."
    if not any(char in "!@#$%^&*()_+-=[]{}|;':\",.<>?/" for char in password):
        return "Password must contain at least one special character."
    return None

def generate_group_pin():
    #Generates a unique 6-character group PIN (digits + uppercase letters).
    while True:
        # Generate a random 6-character PIN
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

        # Open a single database connection
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if the code already exists in the database
        cursor.execute("SELECT 1 FROM Groups WHERE code = ?", (code,))
        existing_code = cursor.fetchone()  # Fetch one result (if any)

        conn.close()  # Close connection after use

        # If no existing group has this code, return it
        if not existing_code:
            return code

def create_group_assistant(group_name, user_id):
    code = generate_group_pin()

    try:
        conn = get_db_connection()  # Get a new database connection
        cursor = conn.cursor()

        # Insert the new group
        cursor.execute("INSERT INTO Groups (name, code, created_by) VALUES (?, ?, ?)", (group_name, code, user_id))
        conn.commit()  # Commit the change

        # Retrieve the newly created group ID
        cursor.execute("SELECT group_id FROM Groups WHERE code = ?", (code,))
        group = cursor.fetchone()  # Fetch a single row

        if not group:
            raise Exception("Group ID retrieval failed")  # Error if no group found

        group_id = group["group_id"]  # Extract the actual group_id value

        # Insert the creator into GroupMembers
        cursor.execute("INSERT INTO GroupMembers (group_id, user_id) VALUES (?, ?)", (group_id, user_id))
        conn.commit()  # Commit the new group member addition

        conn.close()  # Close the connection
        return code  # Return the generated group code if successful

    except Exception as e:
        print(f"Error occurred: {e}")  # Debugging log
        return None  # Return None if an error occurs


class GroupJoinError(Exception):
    """Custom exception for group join errors."""
    pass


def join_group_assistant(group_pin, user_id):
    try:
        conn = get_db_connection()  # Get a new database connection
        cursor = conn.cursor()

        cursor.execute("SELECT group_id FROM Groups WHERE code = ?", (group_pin,))
        group = cursor.fetchone()
        if not group:
            raise GroupJoinError("Wrong group pin entered, no groups with that pin")

        group_id = group["group_id"]  # Extract the actual group_id value

        # Check if the user is already a member of the group
        cursor.execute("SELECT 1 FROM GroupMembers WHERE group_id = ? AND user_id = ?", (group_id, user_id))
        if cursor.fetchone():
            raise GroupJoinError("You are already a member of this group.")

        # Insert the creator into GroupMembers
        cursor.execute("INSERT INTO GroupMembers (group_id, user_id) VALUES (?, ?)", (group_id, user_id))
        conn.commit()  # Commit the new group member addition

        conn.close()  # Close the connection
        return "Joined group sucessfully"

    except GroupJoinError as e:
        conn.close()
        raise e  # Re-raise the error so `app.py` can handle it

    except Exception as e:
        conn.close()
        raise GroupJoinError("An unexpected error occurred while joining the group")










