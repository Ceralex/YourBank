from flask import Flask, redirect, render_template, request, url_for, session, g
import hashlib
import psycopg2
import os
from dotenv import load_dotenv

app = Flask(__name__)

USERNAME = "user"
PASSWORD = "password"

app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

load_dotenv()

DATABASE_URL = os.environ.get('DATABASE_URL')

def check_password(db, username, password):
    cur = db.cursor()
    cur.execute("SELECT password FROM accounts WHERE username = %s", (username,))
    user = cur.fetchone()
    cur.close()
    if user is None:
        return False
    
    password = hashlib.sha256(password.encode()).hexdigest()

    return user[0] == password

def get_balance_infos(db, username):
    cur = db.cursor()
    cur.execute("""SELECT
                        COALESCE(SUM(transfers_in.amount), 0::money) AS total_income,
                        COALESCE(SUM(transactions.amount), 0::money) + COALESCE(SUM(transfers_out.amount), 0::money) AS total_expenses,
                        (COALESCE(SUM(transfers_in.amount), 0::money) 
                        - COALESCE(SUM(transactions.amount), 0::money)
                        - COALESCE(SUM(transfers_out.amount), 0::money))::money AS balance
                    FROM
                        accounts
                    LEFT JOIN transactions ON transactions.bank_account_id = accounts.id
                    LEFT JOIN transfers transfers_in ON transfers_in.receiver_bank_account_id = accounts.id
                    LEFT JOIN transfers transfers_out ON transfers_out.sender_bank_account_id = accounts.id
                    WHERE
                        accounts.username = %s
                    GROUP BY
                        accounts.username;
""",
      (username,))
    infos = cur.fetchone()
    cur.close()

    total_income = infos[0]
    total_expenses = infos[1]
    balance = infos[2]

    return {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "balance": balance
    }

def get_operations(db, username):
    cur = db.cursor()
    cur.execute("""SELECT
                        'Transaction' AS record_type,
                        transactions.amount,
                        transactions.description,
                        to_char(transactions.date, 'YYYY-MM-DD HH24:MI') AS date
                    FROM
                        accounts
                    JOIN transactions ON transactions.bank_account_id = accounts.id
                    WHERE
                        accounts.username = %s

                    UNION ALL

                    SELECT
                        CASE WHEN transfers.sender_bank_account_id = accounts.id THEN 'Transfer sent' ELSE 'Transfer seceived' END AS record_type,
                        CASE WHEN transfers.sender_bank_account_id = accounts.id THEN (-transfers.amount::numeric)::money ELSE transfers.amount END AS amount,
                        transfers.description,
                        to_char(transfers.date, 'YYYY-MM-DD HH24:MI') AS date
                    FROM
                        accounts
                    LEFT JOIN transfers ON transfers.sender_bank_account_id = accounts.id OR transfers.receiver_bank_account_id = accounts.id
                    WHERE
                        accounts.username = %s

                    ORDER BY date DESC;
""",
      (username, username,))
    operations = cur.fetchall()
    cur.close()

    return operations

def create_user(db, username, password):
    password = hashlib.sha256(password.encode()).hexdigest()
    
    cur = db.cursor()
    
    cur.execute("INSERT INTO accounts (username, password) VALUES (%s, %s)", (username, password))

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
        except psycopg2.errors.UniqueViolation:
            return render_template("signup.html", error="Username already exists")
        
        session["username"] = username

        return redirect(url_for("me"))

@app.before_request
def before_request():
    db = psycopg2.connect(DATABASE_URL)
    g.db = db

@app.after_request
def after_request(response):
    g.db.close()

    return response

@app.get("/me")
def me():
    if "username" in session:
        username = session["username"]

        account_infos = get_balance_infos(g.db, username)
        past_operations = get_operations(g.db, username)

        return render_template("me.html", username=username, infos=account_infos, operations=past_operations, len=len(past_operations))
    else:
        return redirect(url_for("index"))

@app.get("/logout")
def logout():
    session.pop("username", None)

    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)