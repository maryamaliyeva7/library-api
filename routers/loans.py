from datetime import date, timedelta

from flask import Blueprint, jsonify, request

import book_repository
import loan_repository
import member_repository
from utils import check, money

bp = Blueprint("loans", __name__)

CURRENT_MEMBER = None


def notify(kind, title="", send=True):
    if not send:
        return
    if kind == "checkout":
        subject = "Book checked out"
        body = "You checked out " + title
    elif kind == "renew":
        subject = "Loan renewed"
        body = "You renewed " + title
    else:
        subject = "Library notice"
        body = title
    with open("outbox.txt", "a") as f:
        f.write("TO: " + CURRENT_MEMBER["email"] + " | SUBJECT: " + subject + " | BODY: " + body + "\n")


@bp.route("/loans", methods=["GET"])
def list_loans():
    result = []
    for loan in loan_repository.list_loans():
        current_fine = loan["fine"]
        days_late = (date.today() - date.fromisoformat(loan["due_date"])).days
        if loan["returned"] == 0:
            current_fine = max(0, days_late) * 0.50
        if request.args.get("overdue") == "true" and (loan["returned"] == 1 or days_late <= 0):
            continue
        result.append(
            {
                "id": loan["id"],
                "book_id": loan["book_id"],
                "member_id": loan["member_id"],
                "due_date": loan["due_date"],
                "returned": bool(loan["returned"]),
                "fine": money(loan["fine"]),
                "fine_paid": bool(loan["fine_paid"]),
                "renewals": loan["renewals"],
                "checked_out": loan["checked_out"],
                "current_fine": money(current_fine),
            }
        )
    return jsonify(result)


@bp.route("/loans/<int:loan_id>", methods=["GET"])
def get_loan(loan_id):
    loan = loan_repository.get_loan(loan_id)
    if loan is None:
        return jsonify({"error": "loan not found"}), 404
    current_fine = loan["fine"]
    if loan["returned"] == 0:
        days_late = (date.today() - date.fromisoformat(loan["due_date"])).days
        current_fine = max(0, days_late) * 0.50
    return jsonify(
        {
            "id": loan["id"],
            "book_id": loan["book_id"],
            "member_id": loan["member_id"],
            "due_date": loan["due_date"],
            "returned": bool(loan["returned"]),
            "fine": money(loan["fine"]),
            "fine_paid": bool(loan["fine_paid"]),
            "renewals": loan["renewals"],
            "checked_out": loan["checked_out"],
            "current_fine": money(current_fine),
        }
    )


@bp.route("/loans", methods=["POST"])
def create_loan():
    global CURRENT_MEMBER
    data = request.get_json(silent=True) or {}
    if not data.get("book_id") or not data.get("member_id"):
        return jsonify({"error": "book_id and member_id are required"}), 400
    if data.get("due_date") and not check(data["due_date"], "date"):
        return jsonify({"error": "invalid due_date"}), 400

    book = book_repository.get_book(data["book_id"])
    if book is None:
        return jsonify({"error": "book not found"}), 404
    member = member_repository.get_member(data["member_id"])
    if member is None:
        return jsonify({"error": "member not found"}), 404
    if book["available"] == 0:
        return jsonify({"error": "book is not available"}), 409

    rows = loan_repository.list_loans_for_member(data["member_id"])
    owed = 0
    open_loans = 0
    for loan in rows:
        if loan["returned"] == 0:
            open_loans += 1
            days_late = (date.today() - date.fromisoformat(loan["due_date"])).days
            if days_late > 0:
                owed += days_late * 0.5
        elif loan["fine_paid"] == 0:
            owed += loan["fine"]
    if owed > 0:
        return jsonify({"error": "member has unpaid fines"}), 409
    limit = 5 if member["type"] == "staff" else 3
    if open_loans >= limit:
        return jsonify({"error": "loan limit reached"}), 409

    today = date.today()
    due_date = data.get("due_date") or (today + timedelta(days=14)).isoformat()
    loan = loan_repository.create_loan(
        data["book_id"], data["member_id"], due_date, today.isoformat()
    )
    book_repository.set_availability(data["book_id"], False)

    CURRENT_MEMBER = member
    notify("checkout", book["title"])

    return (
        jsonify(
            {
                "id": loan["id"],
                "book_id": loan["book_id"],
                "member_id": loan["member_id"],
                "due_date": loan["due_date"],
                "returned": bool(loan["returned"]),
                "fine": money(loan["fine"]),
                "fine_paid": bool(loan["fine_paid"]),
                "renewals": loan["renewals"],
                "checked_out": loan["checked_out"],
            }
        ),
        201,
    )


@bp.route("/loans/<int:loan_id>/return", methods=["POST"])
def return_book(loan_id):
    loan = loan_repository.get_loan(loan_id)
    if loan is None:
        return jsonify({"error": "loan not found"}), 404
    if loan["returned"] == 1:
        return jsonify({"error": "loan already returned"}), 409

    days_late = (date.today() - date.fromisoformat(loan["due_date"])).days
    fine = max(0, days_late) * 0.50
    updated = loan_repository.mark_returned(loan_id, loan["book_id"], fine)
    member = member_repository.get_member(loan["member_id"])
    book = book_repository.get_book(loan["book_id"])

    with open("outbox.txt", "a") as f:
        f.write(
            "TO: " + member["email"] + " | SUBJECT: Book returned | BODY: You returned " + book["title"]
            + ". Fine: $" + str(money(fine)) + "\n"
        )

    return jsonify(
        {
            "id": updated["id"],
            "book_id": updated["book_id"],
            "member_id": updated["member_id"],
            "due_date": updated["due_date"],
            "returned": bool(updated["returned"]),
            "fine": money(updated["fine"]),
            "fine_paid": bool(updated["fine_paid"]),
            "renewals": updated["renewals"],
            "checked_out": updated["checked_out"],
        }
    )


@bp.route("/loans/<int:loan_id>/renew", methods=["POST"])
def renew_loan(loan_id):
    global CURRENT_MEMBER
    loan = loan_repository.get_loan(loan_id)
    if loan is None:
        return jsonify({"error": "loan not found"}), 404
    if loan["returned"] == 1:
        return jsonify({"error": "loan already returned"}), 409
    if date.fromisoformat(loan["due_date"]) < date.today():
        return jsonify({"error": "overdue loans cannot be renewed"}), 409
    if loan["renewals"] >= 1:
        return jsonify({"error": "loan was already renewed"}), 409

    new_due = (date.fromisoformat(loan["due_date"]) + timedelta(days=14)).isoformat()
    updated = loan_repository.extend_loan(loan_id, new_due)
    CURRENT_MEMBER = member_repository.get_member(loan["member_id"])
    book = book_repository.get_book(loan["book_id"])
    notify("renew", book["title"])

    return jsonify(
        {
            "id": updated["id"],
            "book_id": updated["book_id"],
            "member_id": updated["member_id"],
            "due_date": updated["due_date"],
            "returned": bool(updated["returned"]),
            "fine": money(updated["fine"]),
            "fine_paid": bool(updated["fine_paid"]),
            "renewals": updated["renewals"],
            "checked_out": updated["checked_out"],
        }
    )


@bp.route("/loans/<int:loan_id>/pay-fine", methods=["POST"])
def pay_fine(loan_id):
    loan = loan_repository.get_loan(loan_id)
    if loan is None:
        return jsonify({"error": "loan not found"}), 404
    if loan["returned"] == 0:
        return jsonify({"error": "return the book before paying"}), 409
    if loan["fine"] <= 0 or loan["fine_paid"] == 1:
        return jsonify({"error": "no fine to pay"}), 409

    updated = loan_repository.mark_fine_paid(loan_id)
    member = member_repository.get_member(loan["member_id"])
    with open("outbox.txt", "a") as f:
        f.write(
            "TO: " + member["email"] + " | SUBJECT: Fine paid | BODY: We received $"
            + str(money(loan["fine"])) + "\n"
        )

    return jsonify(
        {
            "id": updated["id"],
            "book_id": updated["book_id"],
            "member_id": updated["member_id"],
            "due_date": updated["due_date"],
            "returned": bool(updated["returned"]),
            "fine": money(updated["fine"]),
            "fine_paid": bool(updated["fine_paid"]),
            "renewals": updated["renewals"],
            "checked_out": updated["checked_out"],
        }
    )
