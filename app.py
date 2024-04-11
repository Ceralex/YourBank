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

# Database configuration
DATABASE_URL = os.environ.get('DATABASE_URL')  # Get the database URL from environment variables

def check_password(db, username, password):
    cur = db.cursor()
    cur.execute("SELECT password FROM users WHERE username = %s", (username,))
    user = cur.fetchone()
    cur.close()
    if user is None:
        return False
    return user[0] == password

@app.route("/")
def hello_world():
    return render_template("index.html")

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
        return render_template("private_page.html", username=username)
    else:
        return redirect(url_for("login"))

@app.get("/logout")
def logout():
    session.pop("username", None)

    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template('login.html')
    else:
        username = request.form["username"]
        password = request.form["password"]

        # password = hashlib.sha256(password.encode()).hexdigest()

        db = g.db
        if check_password(db,username, password):
            session["username"] = username
            return redirect(url_for("me"))
        else:
            return "<p>Wrong username or password</p>"


if __name__ == "__main__":
    app.run(debug=True)