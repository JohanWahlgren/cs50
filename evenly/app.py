import os
import re
import datetime

from flask import Flask, flash, redirect, render_template, request, session, url_for, jsonify
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, validate_form_input, validate_password, login_required, settle_algorithm, create_group_assistant, join_group_assistant, GroupJoinError

from database import get_db_connection

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
def home():
    # If the user is logged in, redirect to index
    if "user_id" in session:
        return redirect("/home")

    # Otherwise, show the start page
    return redirect("/start")


@app.route("/home")
@login_required
def home_page():
    # Show all active groups
    user_id = session["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT Groups.group_id, Groups.name
        FROM Groups
        JOIN GroupMembers ON Groups.group_id = GroupMembers.group_id
        WHERE GroupMembers.user_id = ? AND Groups.status = 'active'
    """, (user_id,))
    groups = cursor.fetchall()  # Get all results

    conn.close()  # Close the connection

    return render_template("home.html", groups=groups)


@app.route("/start")
def start():
    return render_template("start.html")

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")
        repeated_password = request.form.get("repeated_password")

        # Check for empty fields or invalid characters
        error = validate_form_input({"username": username, "password": password, "repeated_password": repeated_password})
        if error:
            return apology(error, 400)

        # Validate password
        error = validate_password(password)
        if error:
            return apology(error, 400)

        if password != repeated_password:
            return apology("Please repeat the password identically", 400)

        # Open the database connection once
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if username already exists
        cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
        if cursor.fetchone():  # If a row is returned, the username exists
            conn.close()
            return apology("Username already exists, please choose a unique one.", 400)

        # Hash password and insert new user
        hash_password = generate_password_hash(password)
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, hash_password))
        conn.commit()  # Commit changes

        # Retrieve user_id for session
        cursor.execute("SELECT user_id FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()

        conn.close()  # Close connection after all queries

        if row:
            session["user_id"] = row["user_id"]
        else:
            return apology("Error retrieving user ID", 500)

        #Redirect to homepage
        return redirect("/")

    return render_template("start.html")

@app.route("/login", methods=["GET", "POST"])
def login():

    # Forget any user_id
    session.clear()
    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        # Check for empty fields or invalid characters
        error = validate_form_input({"username": username, "password": password})
        if error:
            return apology(error, 400)

        # Validate password
        error = validate_password(password)
        if error:
            return apology(error, 400)

        # Query database for username
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE username = ?", (request.form.get("username"),))
        rows = cursor.fetchall()  # Fetch all results

        conn.close()

        # Ensure username exists and password is correct
        if not rows or not check_password_hash(rows[0]["password_hash"], password):
            return apology("Invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["user_id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    return render_template("start.html")

@app.route("/logout", methods=["POST"])
@login_required
def logout():

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/start")


@app.route("/active-group/<int:group_id>")
@login_required
def active_group(group_id):

    user_id = session["user_id"]

    # Call settlement function before fetching settlements
    settle_algorithm(group_id)  # This ensures the database is updated

    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch group info
    cursor.execute("SELECT name, timestamp, code FROM Groups WHERE group_id = ?", (group_id,))
    group = cursor.fetchone()
    if not group:
        conn.close()
        return apology("Group not found", 404)

    group_name, created_at, group_code = group

    # Fetch total spent
    cursor.execute("SELECT SUM(amount) FROM Payments WHERE group_id = ?", (group_id,))
    total_spent = cursor.fetchone()[0] or 0

    # Fetch expenses
    cursor.execute("""
        SELECT p.payment_id, p.paid_by, u.username, p.amount, p.description, p.timestamp
        FROM Payments p
        JOIN Users u ON p.paid_by = u.user_id
        WHERE p.group_id = ?
        ORDER BY p.timestamp DESC
    """, (group_id,))
    expenses = [dict(zip(["payment_id", "paid_by", "username", "amount", "description", "timestamp"], row)) for row in cursor.fetchall()]

    # Fetch debts (now including settlement_id and status)
    cursor.execute("""
        SELECT s.settlement_id, s.from_user, u1.username AS from_username,
           s.to_user, u2.username AS to_username, s.amount, s.status
        FROM Settlements s
        JOIN Users u1 ON s.from_user = u1.user_id
        JOIN Users u2 ON s.to_user = u2.user_id
        WHERE s.group_id = ?
        ORDER BY s.timestamp DESC
    """, (group_id,))

    debts = [dict(zip(["settlement_id", "from_user", "from_username", "to_user", "to_username", "amount", "status"], row)) for row in cursor.fetchall()]

    # Fetch group members
    cursor.execute("""
        SELECT user_id, username
        FROM Users
        WHERE user_id IN (SELECT user_id FROM GroupMembers WHERE group_id = ?)
    """, (group_id,))
    group_members = [dict(zip(["user_id", "username"], row)) for row in cursor.fetchall()]

    conn.close()

    return render_template(
        "active_group.html",
        group_name=group_name,
        group_code=group_code,
        created_at=created_at,
        total_spent=total_spent,
        expenses=expenses,
        debts=debts,
        group_id=group_id,
        group_members=group_members,
    )


@app.route("/finished-group/<int:group_id>")
@login_required
def finished_group(group_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch group info (no need for code since it's finished)
    cursor.execute("SELECT name, timestamp FROM Groups WHERE group_id = ?", (group_id,))
    group = cursor.fetchone()
    if not group:
        conn.close()
        return apology("Group not found", 404)

    group_name, created_at = group

    # Fetch total spent
    cursor.execute("SELECT SUM(amount) FROM Payments WHERE group_id = ?", (group_id,))
    total_spent = cursor.fetchone()[0] or 0

    # Fetch expenses
    cursor.execute("""
        SELECT p.payment_id, p.paid_by, u.username, p.amount, p.description, p.timestamp
        FROM Payments p
        JOIN Users u ON p.paid_by = u.user_id
        WHERE p.group_id = ?
        ORDER BY p.timestamp DESC
    """, (group_id,))
    expenses = [dict(zip(["payment_id", "paid_by", "username", "amount", "description", "timestamp"], row)) for row in cursor.fetchall()]

    # Fetch settled debts
    cursor.execute("""
        SELECT u1.username AS from_username,
               u2.username AS to_username,
               s.amount
        FROM Settlements s
        JOIN Users u1 ON s.from_user = u1.user_id
        JOIN Users u2 ON s.to_user = u2.user_id
        WHERE s.group_id = ? AND s.status = 'paid'
        ORDER BY s.timestamp DESC
    """, (group_id,))
    debts = [dict(zip(["from_username", "to_username", "amount"], row)) for row in cursor.fetchall()]

    conn.close()

    return render_template(
        "finished_group.html",
        group_name=group_name,
        created_at=created_at,
        total_spent=total_spent,
        expenses=expenses,
        debts=debts,
        group_id=group_id
    )


@app.route("/add-expense", methods=["POST"])
@login_required
def add_expense():
    if "user_id" not in session:
        return redirect(url_for("login"))

    group_id = request.form.get("group_id")
    paid_by = request.form.get("paid_by")
    description = request.form.get("description")
    amount = request.form.get("amount")
    split_with = request.form.getlist("split_with")

    if not all([group_id, paid_by, description, amount, split_with]):
        return apology("Missing required fields", 400)

    error = validate_form_input({"description": description, "amount": amount})
    if error:
        return apology(error, 400)

    amount = float(amount)

    print("Split with:", split_with)
    print("Unique Split with:", set(split_with))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Insert into Payments table
    cursor.execute(
        "INSERT INTO Payments (group_id, paid_by, amount, description) VALUES (?, ?, ?, ?)",
        (group_id, paid_by, amount, description),
    )
    payment_id = cursor.lastrowid

    # Split amount equally among selected members
    split_amount = round(amount / len(split_with), 2)

    # Insert into PaymentShares table
    for user_id in split_with:
        cursor.execute(
            "INSERT INTO PaymentShares (payment_id, user_id, share) VALUES (?, ?, ?)",
            (payment_id, user_id, split_amount),
        )

    conn.commit()
    conn.close()

    return redirect(url_for("active_group", group_id=group_id))


@app.route("/expense-detail/<int:payment_id>")
@login_required
def expense_detail(payment_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch payment details
    cursor.execute(
        """
        SELECT p.payment_id, p.amount, p.description, p.timestamp, u.username AS paid_by
        FROM Payments p
        JOIN Users u ON p.paid_by = u.user_id
        WHERE p.payment_id = ?
        """,
        (payment_id,),
    )
    payment = cursor.fetchone()

    if not payment:
        conn.close()
        return jsonify({"error": "Expense not found"}), 404

    # Fetch split details
    cursor.execute(
        """
        SELECT u.username, ps.share
        FROM PaymentShares ps
        JOIN Users u ON ps.user_id = u.user_id
        WHERE ps.payment_id = ?
        """,
        (payment_id,),
    )
    splitters = cursor.fetchall()

    conn.close()

    return jsonify({
        "description": payment["description"],
        "amount": payment["amount"],
        "paid_by": payment["paid_by"],
        "timestamp": payment["timestamp"],
        "splitters": [{"username": s["username"], "share": s["share"]} for s in splitters]
    })


@app.route("/settle-debt/<int:settlement_id>", methods=["POST"])
@login_required
def settle_debt(settlement_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get the group_id first since we'll need it for redirect
    cursor.execute("SELECT group_id FROM Settlements WHERE settlement_id = ?", (settlement_id,))
    result = cursor.fetchone()
    if not result:
        conn.close()
        return apology("Settlement not found", 404)

    current_group_id = result["group_id"]

    # Verify user is the creditor before marking as paid
    cursor.execute("""
        UPDATE Settlements
        SET status = 'paid'
        WHERE settlement_id = ?
        AND to_user = ?
    """, (settlement_id, session["user_id"]))

    if cursor.rowcount == 0:  # If no rows were affected, user isn't authorized
        conn.close()
        return apology("You can only settle debts where you should receive a payment", 403)

    conn.commit()

    # Check if all settlements in the group are paid
    cursor.execute("""
        SELECT COUNT(*) AS unpaid_count
        FROM Settlements
        WHERE group_id = ?
        AND status = 'unpaid'
    """, (current_group_id,))
    unpaid_count = cursor.fetchone()["unpaid_count"]

    if unpaid_count == 0:
        # All settlements are paid, mark the group as inactive
        cursor.execute("""
            UPDATE Groups
            SET status = 'inactive'
            WHERE group_id = ?
        """, (current_group_id,))
        conn.commit()
        conn.close()

        flash("The last debt is settled. You will now find this group in your profile.", "success")
        return redirect(url_for('profile'))

    conn.close()

    return redirect(url_for('active_group', group_id=current_group_id))


@app.route("/profile")
@login_required
def profile():
    # Show all finished groups
    user_id = session["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT Groups.group_id, Groups.name
        FROM Groups
        JOIN GroupMembers ON Groups.group_id = GroupMembers.group_id
        WHERE GroupMembers.user_id = ? AND Groups.status = 'inactive'
    """, (user_id,))
    groups = cursor.fetchall()  # Get all results

    conn.close()  # Close the connection

    return render_template("profile.html", groups=groups)


@app.route("/help")
@login_required
def help():
    return render_template("help.html")

@app.route("/change-password", methods=["POST"])
@login_required
def change_password():
    if request.method == "POST":
        # Get form data
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        repeated_new_password = request.form.get("repeated_new_password")

        # Check for empty fields
        if not current_password or not new_password or not repeated_new_password:
            return apology("All fields are required", 400)

        # Validate new password
        error = validate_password(new_password)
        if error:
            return apology(error, 400)

        # Check if new passwords match
        if new_password != repeated_new_password:
            return apology("New passwords do not match", 400)

        # Open database connection
        conn = get_db_connection()
        cursor = conn.cursor()

        # Fetch the user's current password hash
        cursor.execute("SELECT password_hash FROM users WHERE user_id = ?", (session["user_id"],))
        row = cursor.fetchone()

        if not row:
            conn.close()
            return apology("User not found", 404)

        # Verify current password
        if not check_password_hash(row["password_hash"], current_password):
            conn.close()
            return apology("Current password is incorrect", 403)

        # Hash the new password and update the database
        new_password_hash = generate_password_hash(new_password)
        cursor.execute("UPDATE users SET password_hash = ? WHERE user_id = ?", (new_password_hash, session["user_id"]))
        conn.commit()
        conn.close()

        # Notify the user of success
        flash("Password changed successfully!", "success")
        return redirect("/profile")

    return redirect("/")

@app.route("/delete-account")
@login_required
def delete_account():
    pass  # Placeholder for now

@app.route("/create-group", methods=["GET", "POST"])
@login_required
def create_group():

    if request.method == "POST":
        group_name = request.form.get("group_name")
        error = validate_form_input({"group_name": group_name})
        if error:
            return apology(error, 400)

        if len(group_name) > 20:
            return apology("Group name to long", 400)

        user_id = session["user_id"]

        group_code = create_group_assistant(group_name, user_id)

        if group_code is None:
            return apology("Failed to create group", 400)

        # Flash a success message with the generated group code
        flash(f"Group created successfully! Your group PIN is: {group_code}", "success")

        # Redirect to the home page or another page as needed
        return redirect("/home")

    return render_template("start.html")

@app.route("/join-group", methods=["GET", "POST"])
@login_required
def join_group():

    if request.method == "POST":
        group_pin = request.form.get("group_pin")

        error = validate_form_input({"group_pin": group_pin})
        if error:
            return apology(error, 400)

        user_id = session["user_id"]

        try:
            message = join_group_assistant(group_pin, user_id)
            flash(message)
            return redirect("/home")  # Redirect to the home page after success

        except GroupJoinError as e:
            return apology(str(e), 400)  # Show the error in UI

    return render_template("start.html")



@app.route("/clear_error")
def clear_error():
    """Clear the error message from session after showing the modal"""
    session.pop("error", None)
    return "", 204  # Return empty response to signify success






