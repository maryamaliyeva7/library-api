from datetime import date

from flask import Blueprint, jsonify, request

import loan_repository
import member_repository
from utils import check, money

bp = Blueprint("members", __name__)


@bp.route("/members", methods=["GET"])
def list_members():
    result = []
    for member in member_repository.list_members():
        result.append(
            {
                "id": member["id"],
                "name": member["name"],
                "email": member["email"],
                "type": member["type"],
            }
        )
    return jsonify(result)


@bp.route("/members/<int:member_id>", methods=["GET"])
def get_member(member_id):
    member = member_repository.get_member(member_id)
    if member is None:
        return jsonify({"error": "member not found"}), 404
    return jsonify(
        {
            "id": member["id"],
            "name": member["name"],
            "email": member["email"],
            "type": member["type"],
        }
    )


@bp.route("/members", methods=["POST"])
def create_member():
    data = request.get_json(silent=True) or {}
    if not data.get("name"):
        return jsonify({"error": "name is required"}), 400
    if not check(data.get("email"), "email"):
        return jsonify({"error": "invalid email"}), 400
    member_type = data.get("type", "student")
    if not check(member_type, "member_type"):
        return jsonify({"error": "type must be student or staff"}), 400
    if member_repository.get_member_by_email(data["email"]) is not None:
        return jsonify({"error": "email already registered"}), 409
    member = member_repository.create_member(data["name"], data["email"], member_type)
    return jsonify(
        {
            "id": member["id"],
            "name": member["name"],
            "email": member["email"],
            "type": member["type"],
        }
    ), 201


@bp.route("/members/<int:member_id>/loans", methods=["GET"])
def member_loans(member_id):
    member = member_repository.get_member(member_id)
    if member is None:
        return jsonify({"error": "member not found"}), 404
    rows = loan_repository.list_loans_for_member(member_id)
    owed = 0
    open_loans = 0
    loans = []
    for loan in rows:
        if loan["returned"] == 0:
            open_loans += 1
            days_late = (date.today() - date.fromisoformat(loan["due_date"])).days
            if days_late > 0:
                owed += days_late * 0.5
        elif loan["fine_paid"] == 0:
            owed += loan["fine"]
        loans.append(
            {
                "id": loan["id"],
                "book_id": loan["book_id"],
                "due_date": loan["due_date"],
                "returned": bool(loan["returned"]),
                "fine": money(loan["fine"]),
                "fine_paid": bool(loan["fine_paid"]),
            }
        )
    limit = 5 if member["type"] == "staff" else 3
    return jsonify(
        {
            "loans": loans,
            "total_owed": money(owed),
            "loans_remaining": limit - open_loans,
        }
    )
