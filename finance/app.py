import os
import re
import datetime

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    user_id = session["user_id"]

    stock_portfolio = db.execute("SELECT symbol, SUM(shares) AS shares FROM transactions WHERE user_id = ? GROUP BY symbol", user_id)
    total_all_value = 0.0

    try:
        for stock in stock_portfolio:
            symbol = stock["symbol"]
            stock_info = lookup(symbol)

            current_price = float(stock_info["price"])
            total_spec_stock = current_price * stock["shares"]

            stock.update({"current_price": current_price, "total_spec_stock": total_spec_stock})

            total_all_value += float(total_spec_stock)
    except (ValueError, KeyError):
        return apology("There is an issue in fetching your stock, please contact support.")

    user_cash = float(db.execute("SELECT cash FROM users WHERE id = ?", user_id)[0]["cash"])
    total_all_value += user_cash

    return render_template("index.html",
    stock_portfolio = stock_portfolio,
    user_cash = user_cash,
    total_all_value = total_all_value)



@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        user_id = session["user_id"]

        symbol = request.form.get("symbol")
        if not symbol:
            return apology("Please enter a symbol.")

        stock = lookup(symbol)
        if stock is None:
            return apology("Symbol does not exist.")

        shares = request.form.get("shares")
        try:
            shares = int(shares)
            if shares <= 0:
                return apology("Number of shares must be greater than 0.")
        except ValueError:
            return apology("Invalid number of shares.")

        transaction_value = shares * stock["price"]

        user_cash = db.execute("SELECT cash FROM users WHERE id = ?", user_id)[0]["cash"]

        if user_cash < transaction_value:
            return apology("Not enough money in account :(")

        date_and_time = datetime.datetime.now()
        genre = "buy"

        db.execute("INSERT INTO transactions (user_id, symbol, shares, price, date, genre) VALUES (?, ?, ?, ?, ?, ?)",
        user_id,
        stock["symbol"],
        shares,
        stock["price"],
        date_and_time,
        genre)

        flash(f"Successfully bought {shares} shares of {symbol} for {transaction_value}")

        updated_user_cash = user_cash - transaction_value
        db.execute("UPDATE users SET cash = ? WHERE id = ?", updated_user_cash, user_id)

        return redirect("/")

    return render_template("buy.html")

@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    user_id = session["user_id"]

    transaction_history = db.execute("SELECT symbol, shares, price, date, genre FROM transactions WHERE user_id = ?", user_id)
    return render_template("history.html", transaction_history=transaction_history)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":
        symbol = request.form.get("symbol")
        stock = lookup(symbol)

        if not stock:
            return apology("Please enter a valid symbol.")

        stock["price"] = usd(stock["price"])

        return render_template("quoted.html", stock=stock)

    return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "GET":
        return render_template("registration.html")

    username = request.form.get("username")
    password = request.form.get("password")
    repeated_password = request.form.get("confirmation")

    if any(not field for field in [username, password, repeated_password]):
        return apology("please fill in all fields.", 400)

    if len(username) < 5 and not username.isalnum():
        return apology("Make sure the username is at least 5 characters long and ONLY contains letters and/or numbers.", 400)

    if len(password) < 7:
        return apology("Password has to be at least 7 characters long", 400)
    if not check_ok_password(password):
        return apology("Password must contain at least one letter, number and special character.", 400)

    if not password == repeated_password:
        return apology("Original password and the repeated one do not match, please try again.", 400)

    if len(db.execute("SELECT username FROM users WHERE username = ?", username)) > 0:
        return apology("Username already exists, please change to a unique one.", 400)

    hash_password = generate_password_hash(password)
    db.execute("INSERT INTO users (username, hash) VALUES(?, ?)",
               username,
               hash_password)

    # Remember which user has logged in
    rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )
    session["user_id"] = rows[0]["id"]

    #Redirect to homepage
    return redirect("/")


def check_ok_password(password):
    SYMBOLS = ["!", "@", "#", "$", "%", "^", "&", "*", "(", ")", ",", "-", "_"]
    symbol_string = "".join(SYMBOLS)

    if (
        re.search("[a-zA-Z]", password) and
        re.search("[0-9]", password) and
        re.search(f"[{re.escape(symbol_string)}]", password)
    ):
        return True
    else:
        return False


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    user_id = session["user_id"]

    if request.method == "GET":
        symbols = db.execute("SELECT symbol FROM transactions WHERE user_id = ? GROUP BY symbol HAVING SUM(shares) > 0", user_id)

        # Debugging: Print the fetched symbols
        print("Fetched symbols:", symbols)

        available_symbols = [row["symbol"] for row in symbols]

        # Debugging: Print the list of available symbols
        print("Available symbols for template:", available_symbols)

        return render_template("sell.html", available_symbols=available_symbols)

    if request.method == "POST":
        symbol = request.form.get("symbol")

        if not lookup(request.form.get("symbol")):
            return apology("Please enter a valid symbol")

        shares_sell = int(request.form.get("shares"))

        db_stock = db.execute("SELECT symbol, SUM(shares) AS shares_have FROM transactions WHERE user_id = ? GROUP BY symbol", user_id)

        user_owns_stock = False

        for row in db_stock:
            if symbol == row["symbol"]:
                user_owns_stock = True
                if shares_sell > row["shares_have"] or shares_sell < 1:
                    return apology("Entered shares are 0 or exceeds amount owned.")
                break

        if not user_owns_stock:
            return apology("Please enter the symbol of a stock you own.")

        stock = lookup(symbol)

        sell_price = shares_sell * stock["price"]

        user_cash_db = db.execute("SELECT cash FROM users WHERE id = ?", user_id)
        user_cash = user_cash_db[0]["cash"]

        user_cash += sell_price
        date = datetime.datetime.now()
        genre = "sell"

        db.execute("INSERT INTO transactions (user_id, symbol, shares, price, date, genre) VALUES (?, ?, ?, ?, ?, ?)", user_id, symbol, (-1)*shares_sell, stock["price"], date, genre)
        db.execute("UPDATE users SET cash = ? WHERE id = ?", user_cash, user_id)

        flash(f"Sold {shares_sell} shares of {symbol} for {sell_price}")
        return redirect("/")

@app.route("/profile", methods=["GET", "POST"])
@login_required
def change_password():
    """Change the user password"""

    if request.method == "POST":
        user_id = session["user_id"]

        username = request.form.get("username")
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")

        db_user = db.execute("SELECT username, hash FROM users WHERE id = ?", user_id)

        # Ensure username belongs to the session logged in and exists and current password is correct
        if len(db_user) != 1 or db_user[0]["username"] != username or not check_password_hash(
            db_user[0]["hash"], current_password
        ):
            return apology("invalid username and/or current password", 403)

        if not check_ok_password(new_password) or len(new_password) < 7:
            return apology("The new password must be at least 7 characters long, contain at least one letter, number and special character.", 403)

        hash_new_password = generate_password_hash(new_password)

        db.execute("UPDATE users SET hash = ? WHERE id = ?", hash_new_password, user_id)
        flash("Successfully changed password!")

        return redirect("/")
    return render_template("profile.html")








