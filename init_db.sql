CREATE TABLE IF NOT EXISTS accounts (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    username   TEXT NOT NULL UNIQUE,
    password   CHAR(64) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS transactions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    amount          REAL NOT NULL,
    description     TEXT NOT NULL,
    bank_account_id INTEGER REFERENCES accounts,
    date            TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS transfers (
    id                       INTEGER PRIMARY KEY AUTOINCREMENT,
    amount                   REAL NOT NULL,
    description              TEXT NOT NULL,
    sender_bank_account_id   INTEGER REFERENCES accounts,
    receiver_bank_account_id INTEGER REFERENCES accounts,
    date                     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);