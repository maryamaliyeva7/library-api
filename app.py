import os
from datetime import date, timedelta
from utils import check, money

from flask import Flask, jsonify, request
from routers.books import bp as books_bp
from routers.members import bp as members_bp
from routers.loans import bp as loans_bp

import db
from db import init_db

app = Flask(__name__)
app.register_blueprint(books_bp)
app.register_blueprint(members_bp)
app.register_blueprint(loans_bp)


# ---------- books ----------

# ---------- members ----------

# ---------- loans ----------

# ---------- reports ----------


@app.route("/reports/overdue", methods=["GET"])
def report_overdue():
    conn = db.connect()
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
    conn = db.connect()
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
