from flask import Blueprint, jsonify, request

import loan_service
from fines import money

bp = Blueprint("loans", __name__)


def loan_json(loan, include_current_fine=False):
    result = {
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
    if include_current_fine:
        result["current_fine"] = loan_service.current_fine(loan)
    return result


@bp.route("/loans", methods=["GET"])
def list_loans():
    only_overdue = request.args.get("overdue") == "true"
    return jsonify(
        [loan_json(loan, include_current_fine=True) for loan in loan_service.list_loans(only_overdue)]
    )


@bp.route("/loans/<int:loan_id>", methods=["GET"])
def get_loan(loan_id):
    return jsonify(loan_json(loan_service.get_loan(loan_id), include_current_fine=True))


@bp.route("/loans", methods=["POST"])
def create_loan():
    data = request.get_json(silent=True) or {}
    return jsonify(loan_json(loan_service.create_loan(data))), 201


@bp.route("/loans/<int:loan_id>/return", methods=["POST"])
def return_book(loan_id):
    return jsonify(loan_json(loan_service.return_book(loan_id)))


@bp.route("/loans/<int:loan_id>/renew", methods=["POST"])
def renew_loan(loan_id):
    return jsonify(loan_json(loan_service.renew_loan(loan_id)))


@bp.route("/loans/<int:loan_id>/pay-fine", methods=["POST"])
def pay_fine(loan_id):
    return jsonify(loan_json(loan_service.pay_fine(loan_id)))
