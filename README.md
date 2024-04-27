# Relazione Tecnica - YourBank

## Introduzione

Questo progetto è un'applicazione web che simula una banca virtuale e alcune sue funzionalità di base: la creazione di un account personale con la visione dei propri bilanci, la possibilità di fare un deposito, una transazione o un bonifico ad un altro utente.

## Tecnologie Utilizzate

- Python 3
- Flask Web Framework
- Database Sqlite
- TailwindCSS
- Flowbite Components

## Architettura del Sistema

L'applicazione è suddivisa in due file python, l'app.py principale e il services.py.
Nel file app.py è presente la gestione delle routes e la parte più legata alle pagine web, mentre in services.py ci sono le funzioni che operano sul database.
Tutti i template web sono nella cartella omonima; ho optato per utilizzarne uno di base (\_base.html) in cui sono inclusi tutti gli headers, compresa la cdn di tailwind, da cui derivano tutte le altre pagine.

## Database

- La tabella account viene utilizzata per l'autenticazione
- La tabella transactions e transfers per le transazioni e i bonifici. Un deposito fatto dall'utente viene inserito come un bonifico con sender NULL.

```sql
CREATE TABLE accounts (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    username   TEXT NOT NULL UNIQUE,
    password   CHAR(64) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE transactions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    amount          REAL NOT NULL,
    description     TEXT NOT NULL,
    bank_account_id INTEGER REFERENCES accounts,
    date            TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE transfers (
    id                       INTEGER PRIMARY KEY AUTOINCREMENT,
    amount                   REAL NOT NULL,
    description              TEXT NOT NULL,
    sender_bank_account_id   INTEGER REFERENCES accounts,
    receiver_bank_account_id INTEGER REFERENCES accounts,
    date                     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Sviluppo del Software

Tutto lo sviluppo del progetto è stato eseguito utilizzando git ed effettuando commit ad ogni nuova feature, o bug fix, effettuato. <br>All'inizio dello sviluppo ho definito le user stories con una descrizione dei requisiti dell'applicazione finale.

## User Stories e Requisiti

- Who? User
  <br>
  What? Sign up and login
  <br>
  How? With a specific form

- Who? User
  <br>
  What? See his balance and his operations history
  <br>
  How? With a nice UI

- Who? User
  <br>
  What? Add transactions
  <br>
  How? With a form and a add button

- Who? User
  <br>
  What? Make transfer to another user
  <br>
  How? With a form and the other's username

- Who? User
  <br>
  What? Make deposit to his bank account
  <br>
  How? With a form with an amount selection

## Deploy e Manutenzione

Per il deploy ho sfruttato l'ambiene di python anywhere, il quale mi ha permesso di clonare la mia repository di git nella loro macchina virtuale remota e configurare con facilità l'hosting della mia applicazione.

## Conclusioni

Questo progetto è ancora in uno stato embrionale e possiede i minimi requisiti che un'applicazione di questo genere necessita, ma è una buona base per una possibile estensione futura.
