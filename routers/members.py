from flask import Blueprint, jsonify, request

import member_service
from fines import money

bp = Blueprint("members", __name__)


def member_json(member):
    return {
        "id": member["id"],
        "name": member["name"],
        "email": member["email"],
        "type": member["type"],
    }


def loan_json(loan):
    return {
        "id": loan["id"],
        "book_id": loan["book_id"],
        "due_date": loan["due_date"],
        "returned": bool(loan["returned"]),
        "fine": money(loan["fine"]),
        "fine_paid": bool(loan["fine_paid"]),
    }


@bp.route("/members", methods=["GET"])
def list_members():
    return jsonify([member_json(member) for member in member_service.list_members()])


@bp.route("/members/<int:member_id>", methods=["GET"])
def get_member(member_id):
    return jsonify(member_json(member_service.get_member(member_id)))


@bp.route("/members", methods=["POST"])
def create_member():
    data = request.get_json(silent=True) or {}
    return jsonify(member_json(member_service.create_member(data))), 201


@bp.route("/members/<int:member_id>/loans", methods=["GET"])
def member_loans(member_id):
    account = member_service.member_account(member_id)
    return jsonify(
        {
            "loans": [loan_json(loan) for loan in account["loans"]],
            "total_owed": money(account["total_owed"]),
            "loans_remaining": account["loans_remaining"],
        }
    )
