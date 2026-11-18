from flask import Blueprint, jsonify

import report_service

bp = Blueprint("reports", __name__)


@bp.route("/reports/overdue", methods=["GET"])
def report_overdue():
    return jsonify(report_service.overdue_report())


@bp.route("/reports/summary", methods=["GET"])
def report_summary():
    return jsonify(report_service.summary_report())
