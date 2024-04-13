from flask import Flask, redirect, render_template, request, url_for, session, g
import sqlite3 as sq
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
    return user[0] == password

def get_balance_infos(db, username):
    cur = db.cursor()
    cur.execute("""SELECT
                        accounts.username,
                        SUM(COALESCE(transactions.amount, 0::money)) AS transaction_total,
                        SUM(COALESCE(transfers_in.amount, 0::money)) AS received_transfers_total,
                        SUM(COALESCE(transfers_out.amount, 0::money)) AS sent_transfers_total,
                        SUM(COALESCE(transfers_in.amount, 0::money))
                        - SUM(COALESCE(transactions.amount, 0::money))
                        - SUM(COALESCE(transfers_out.amount, 0::money))::money AS balance
                    FROM
                        accounts
                    LEFT JOIN transactions ON transactions.bank_account_id = accounts.id
                    LEFT JOIN transfers transfers_in ON transfers_in.receiver_bank_account_id = accounts.id
                    LEFT JOIN transfers transfers_out ON transfers_out.sender_bank_account_id = accounts.id
                    WHERE
                        accounts.username = %s
                    GROUP BY
                        accounts.username;""",
      (username,))
    infos = cur.fetchone()
    cur.close()

    total_transactions = infos[1]
    total_received_transfers = infos[2]
    total_sent_transfers = infos[3]
    balance = infos[4]

    return {
        "total_transactions": total_transactions,
        "total_received_transfers": total_received_transfers,
        "total_sent_transfers": total_sent_transfers,
        "balance": balance
    }

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

        infos = get_balance_infos(g.db, username)
        return render_template("me.html", username=username, infos=infos)
    else:
        return redirect(url_for("index"))

@app.get("/logout")
def logout():
    session.pop("username", None)

    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)