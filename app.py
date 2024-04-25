from flask import Flask, redirect, render_template, request, url_for, session, g
import hashlib
import sqlite3
from decimal import Decimal

app = Flask(__name__)

app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

def check_password(db, username, password):
    cur = db.cursor()
    cur.execute("SELECT password FROM accounts WHERE username = ?", (username,))
    user = cur.fetchone()
    cur.close()
    if user is None:
        return False
    
    password = hashlib.sha256(password.encode()).hexdigest()

    return user[0] == password

def get_balance_infos(db, username):
    cur = db.cursor()
    cur.execute("""SELECT
                        COALESCE(SUM(transactions.amount), 0) AS transactions_out
                    FROM
                        accounts
                    JOIN transactions ON transactions.bank_account_id = accounts.id
                    WHERE
                        accounts.username = ?;
    """, (username,))
    transactions_out = Decimal(cur.fetchone()[0])

    cur.execute("""SELECT
                        COALESCE(SUM(transfers_in.amount), 0) AS transfers_in
                    FROM
                        accounts
                    JOIN transfers as transfers_in ON transfers_in.receiver_bank_account_id = accounts.id
                    WHERE
                        accounts.username = ?;
    """, (username,))
    transfers_in = Decimal(cur.fetchone()[0])
    
    cur.execute("""SELECT
                        COALESCE(SUM(transfers_out.amount), 0) AS transfers_out
                    FROM
                        accounts
                    JOIN transfers as transfers_out ON transfers_out.sender_bank_account_id = accounts.id
                    WHERE
                        accounts.username = ?;
    """, (username,))
                
    transfers_out = Decimal(cur.fetchone()[0])

    cur.close()

    total_income = transfers_in
    total_expenses = transfers_out + transactions_out

    balance = total_income - total_expenses

    return {
        "total_income": f"{total_income:.2f}",
        "total_expenses": f"{total_expenses:.2f}",
        "balance": f"{balance:.2f}"
    }

def get_operations(db, username):
    cur = db.cursor()
    cur.execute("""SELECT
                        'Transaction' AS record_type,
                        -transactions.amount,
                        transactions.description,
                        strftime('%Y-%m-%d %H:%M', transactions.date) AS date
                    FROM
                        accounts
                    JOIN transactions ON transactions.bank_account_id = accounts.id
                    WHERE
                        accounts.username = ?

                    UNION ALL

                    SELECT
                        CASE WHEN transfers.sender_bank_account_id = accounts.id THEN 'Transfer sent' ELSE 'Transfer received' END AS record_type,
                        CASE WHEN transfers.sender_bank_account_id = accounts.id THEN -transfers.amount ELSE transfers.amount END AS amount,
                        transfers.description,
                        strftime('%Y-%m-%d %H:%M', transfers.date) AS date
                    FROM
                        accounts
                    LEFT JOIN transfers ON transfers.sender_bank_account_id = accounts.id OR transfers.receiver_bank_account_id = accounts.id
                    WHERE
                        accounts.username = ? AND transfers.amount IS NOT NULL

                    ORDER BY date DESC;
""",
      (username, username))
    operations = cur.fetchall()
    cur.close()

    # Format each operation amount as money
    formatted_operations = []
    for record_type, amount, description, date in operations:
        formatted_amount = f"{Decimal(amount):.2f}"  # Formatting the amount as a string with two decimal places
        formatted_operations.append((record_type, formatted_amount, description, date))

    return formatted_operations

def create_user(db, username, password):
    password = hashlib.sha256(password.encode()).hexdigest()
    
    cur = db.cursor()
    
    cur.execute("INSERT INTO accounts (username, password) VALUES (?, ?)", (username, password,))

    db.commit()
    cur.close()

def add_transaction(db, username, amount, description):
    cur = db.cursor()

    cur.execute("SELECT id FROM accounts WHERE username = ?", (username,))
    account_id = cur.fetchone()[0]

    cur.execute("INSERT INTO transactions (bank_account_id, amount, description) VALUES (?, ?, ?)", (account_id, amount, description))

    db.commit()
    cur.close()

@app.get("/")
def index():
    return render_template('index.html')

@app.post("/login")
def login():
    username = request.form["username"]
    password = request.form["password"]

    db = g.db
    if check_password(db, username, password):
        session["username"] = username
        return redirect(url_for("me"))
    else:
        return render_template("index.html", error="Invalid username or password")

@app.get("/logout")
def logout():
    session.pop("username", None)

    return redirect(url_for("index"))

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")
    elif request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        repeat_password = request.form["repeat-password"]

        if password != repeat_password:
            return render_template("signup.html", error="Passwords do not match")

        db = g.db

        try:
            create_user(db, username, password)
        except sqlite3.IntegrityError:
            return render_template("signup.html", error="Username already taken")
        
        session["username"] = username

        return redirect(url_for("me"))

@app.before_request
def before_request():
    db = sqlite3.connect("bank.sqlite")
    g.db = db

@app.after_request
def after_request(response):
    g.db.close()

    return response

@app.get("/me")
def me():
    if "username" not in session:
        return redirect(url_for("index"))
    
    username = session["username"]

    account_infos = get_balance_infos(g.db, username)
    past_operations = get_operations(g.db, username)

    return render_template("me.html", username=username, infos=account_infos, operations=past_operations, len=len(past_operations))
        

@app.route("/transaction", methods=["GET", "POST"])
def transaction():
    if request.method == "GET":
        return render_template("make_transaction.html")
    elif request.method == "POST":
        if "username" not in session:
            return redirect(url_for("index"))

        username = session["username"]

        amount = request.form["amount"]
        description = request.form["description"]

        if amount.count(",") > 1:
            return render_template("make_transaction.html", error="Invalid amount")
        
        amount = amount.strip().replace(",", ".")

        try:
            Decimal(amount)
        except:
            return render_template("make_transaction.html", error="Invalid amount")
                
        if float(amount) <= 0:
            return render_template("make_transaction.html", error="Invalid amount")
        
        add_transaction(g.db, username, amount, description)

        return redirect(url_for("me"))


if __name__ == "__main__":
    app.run(debug=True)