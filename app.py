import os
import sqlite3
from datetime import date, timedelta
from utils import check, money

from flask import Flask, jsonify, request
from routers.books import bp as books_bp
from routers.members import bp as members_bp
from routers.loans import bp as loans_bp

app = Flask(__name__)
app.register_blueprint(books_bp)
app.register_blueprint(members_bp)
app.register_blueprint(loans_bp)


def init_db():
    conn = sqlite3.connect("library.db")
    conn.executescript(
        """
        DROP TABLE IF EXISTS books;
        DROP TABLE IF EXISTS members;
        DROP TABLE IF EXISTS loans;
        CREATE TABLE books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT, author TEXT, isbn TEXT, available INTEGER DEFAULT 1
        );
        CREATE TABLE members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, email TEXT UNIQUE, type TEXT
        );
        CREATE TABLE loans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER, member_id INTEGER, due_date TEXT,
            returned INTEGER DEFAULT 0, fine REAL DEFAULT 0,
            fine_paid INTEGER DEFAULT 0, renewals INTEGER DEFAULT 0,
            checked_out TEXT
        );
        """
    )
    books = [
        ("Clean Code", "Robert C. Martin", "9780132350884", 1),
        ("The Pragmatic Programmer", "Andrew Hunt", "9780135957059", 1),
        ("Design Patterns", "Erich Gamma", "9780201633610", 1),
        ("Refactoring", "Martin Fowler", "9780134757599", 1),
        ("Code Complete", "Steve McConnell", "9780735619678", 0),
    ]
    conn.executemany("INSERT INTO books (title, author, isbn, available) VALUES (?, ?, ?, ?)", books)
    members = [
        ("Sam Rivera", "sam@campus.edu", "student"),
        ("Dr. Noor Aziz", "noor@campus.edu", "staff"),
        ("Alex Chen", "alex@campus.edu", "student"),
    ]
    conn.executemany("INSERT INTO members (name, email, type) VALUES (?, ?, ?)", members)
    today = date.today()
    conn.execute(
        "INSERT INTO loans (book_id, member_id, due_date, checked_out) VALUES (5, 3, ?, ?)",
        ((today - timedelta(days=5)).isoformat(), (today - timedelta(days=19)).isoformat()),
    )
    conn.commit()
    conn.close()


# ---------- books ----------

# ---------- members ----------

# ---------- loans ----------

# ---------- reports ----------


@app.route("/reports/overdue", methods=["GET"])
def report_overdue():
    conn = sqlite3.connect("library.db")
    rows = conn.execute(
        """
        SELECT loans.id, books.title, members.name, loans.due_date
        FROM loans
        JOIN books ON books.id = loans.book_id
        JOIN members ON members.id = loans.member_id
        WHERE loans.returned = 0
        """
    ).fetchall()
    conn.close()
    items = []
    total = 0
    for r in rows:
        days_late = (date.today() - date.fromisoformat(r[3])).days
        if days_late > 0:
            fine = days_late * 0.5
            total += fine
            items.append(
                {"loan_id": r[0], "title": r[1], "member": r[2], "days_late": days_late, "fine": money(fine)}
            )
    return jsonify({"items": items, "total_fines": money(total)})


@app.route("/reports/summary", methods=["GET"])
def report_summary():
    conn = sqlite3.connect("library.db")
    total_books = conn.execute("SELECT COUNT(*) FROM books").fetchone()[0]
    rows = conn.execute("SELECT * FROM loans").fetchall()
    conn.close()
    on_loan = 0
    outstanding = 0
    for loan in rows:
        if loan[4] == 0:
            on_loan += 1
            days_late = (date.today() - date.fromisoformat(loan[3])).days
            outstanding += max(0, days_late) * 0.50
        elif loan[6] == 0:
            outstanding += loan[5]
    return jsonify({"total_books": total_books, "on_loan": on_loan, "fines_outstanding": money(outstanding)})


if not os.path.exists("library.db"):
    init_db()
