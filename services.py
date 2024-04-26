from decimal import Decimal
import hashlib


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
                        CASE
                            WHEN transfers.sender_bank_account_id = accounts.id THEN 'Transfer sent'
                            WHEN transfers.sender_bank_account_id IS NULL THEN 'Deposit' -- Handle deposit case
                            ELSE 'Transfer received'
                        END AS record_type,
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

def get_account_id(db, username):
    cur = db.cursor()
    cur.execute("SELECT id FROM accounts WHERE username = ?", (username,))
    account_id = cur.fetchone()

    if account_id is not None:
        account_id = account_id[0]
    
    cur.close()

    return account_id

def make_transfer(db, sender, receiver, amount, description):
    cur = db.cursor()

    cur.execute("SELECT id FROM accounts WHERE username = ?", (sender,))
    sender_id = cur.fetchone()[0]

    cur.execute("SELECT id FROM accounts WHERE username = ?", (receiver,))
    receiver_id = cur.fetchone()[0]

    cur.execute("INSERT INTO transfers (sender_bank_account_id, receiver_bank_account_id, amount, description) VALUES (?, ?, ?, ?)", (sender_id, receiver_id, amount, description))

    db.commit()
    cur.close()

def make_deposit(db, username, amount):
    cur = db.cursor()

    cur.execute("SELECT id FROM accounts WHERE username = ?", (username,))
    account_id = cur.fetchone()[0]

    cur.execute("INSERT INTO transfers (receiver_bank_account_id, amount, description) VALUES (?, ?, 'Deposit')", (account_id, amount))

    db.commit()
    cur.close()