import os
from datetime import date, timedelta
from utils import check, money

from flask import Flask, jsonify, request
from routers.books import bp as books_bp
from routers.members import bp as members_bp
from routers.loans import bp as loans_bp

import db
from db import init_db

import book_repository
import loan_repository
import report_repository

app = Flask(__name__)
app.register_blueprint(books_bp)
app.register_blueprint(members_bp)
app.register_blueprint(loans_bp)


# ---------- books ----------

def book_json(book):
    return {"id": book["id"], "title": book["title"], "author": book["author"], "isbn": book["isbn"], "available": bool(book["available"])}


@app.route("/books", methods=["GET"])
def list_books():
    rows = book_repository.list_books(request.args.get("available") == "true")
    result = []
    for r in rows:
        result.append(book_json(r))
    return jsonify(result)


@app.route("/books/<int:book_id>", methods=["GET"])
def get_book(book_id):
    r = book_repository.get_book(book_id)
    if r is None:
        return jsonify({"error": "book not found"}), 404
    return jsonify(book_json(r))


@app.route("/books", methods=["POST"])
def create_book():
    data = request.get_json(silent=True) or {}
    if not data.get("title") or not data.get("author"):
        return jsonify({"error": "title and author are required"}), 400
    if not check(data.get("isbn"), "isbn"):
        return jsonify({"error": "invalid isbn"}), 400
    r = book_repository.create_book(data["title"], data["author"], data["isbn"])
    return jsonify(book_json(r)), 201


@app.route("/books/<int:book_id>", methods=["DELETE"])
def delete_book(book_id):
    r = book_repository.get_book(book_id)
    if r is None:
        return jsonify({"error": "book not found"}), 404
    if r["available"] == 0:
        return jsonify({"error": "book is on loan"}), 409
    book_repository.delete_book(book_id)
    return "", 204


# ---------- members ----------

# ---------- loans ----------

# ---------- reports ----------


@app.route("/reports/overdue", methods=["GET"])
def report_overdue():
    rows = report_repository.list_open_loans_with_details()
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
    total_books = book_repository.count_books()
    rows = loan_repository.list_loans()
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
