from flask import Flask, redirect, render_template, request, url_for, session, g
from services import add_transaction, check_password, create_user, get_account_id, get_balance_infos, get_operations, make_deposit, make_transfer
import sqlite3
from decimal import Decimal

app = Flask(__name__)

app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

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
    if "username" not in session:
        return redirect(url_for("index"))
    
    if request.method == "GET":
        return render_template("make_transaction.html")
    elif request.method == "POST":
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
        
        balance = get_balance_infos(g.db, username).get("balance")
        
        if Decimal(balance) - Decimal(amount) < 0:
            return render_template("make_transaction.html", error="Insufficient funds")
        
        add_transaction(g.db, username, amount, description)

        return redirect(url_for("me"))

@app.route("/transfer", methods=["GET", "POST"])
def transfer():
    if "username" not in session:
        return redirect(url_for("index"))

    if request.method == "GET":
        return render_template("make_transfer.html")
    elif request.method == "POST":
        username = session["username"]

        beneficiary = request.form["beneficiary"]
        amount = request.form["amount"]
        description = request.form["description"]

        if amount.count(",") > 1:
            return render_template("make_transfer.html", error="Invalid amount")
        
        amount = amount.strip().replace(",", ".")

        try:
            Decimal(amount)
        except:
            return render_template("make_transfer.html", error="Invalid amount")
                
        if float(amount) <= 0:
            return render_template("make_transfer.html", error="Invalid amount")
        

        beneficiary_id = get_account_id(g.db, beneficiary)

        if beneficiary_id is None:
            return render_template("make_transfer.html", error="Beneficiary not found")

        balance = get_balance_infos(g.db, username).get("balance")

        if Decimal(balance) - Decimal(amount) < 0:
            return render_template("make_transfer.html", error="Insufficient funds")

        make_transfer(g.db, username, beneficiary, amount, description)

        return redirect(url_for("me"))

@app.route("/deposit", methods=["GET", "POST"])
def deposit():
    if "username" not in session:
        return redirect(url_for("index"))

    if request.method == "GET":
        return render_template("make_deposit.html")
    elif request.method == "POST":
        username = session["username"]

        amount = request.form["amount"]
        
        make_deposit(g.db, username, amount)

        return redirect(url_for("me"))

if __name__ == "__main__":
    app.run(debug=True)