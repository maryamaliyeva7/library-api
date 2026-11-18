import os

from flask import Flask, jsonify

import report_service
from db import init_db
from errors import LibraryError
from routers.books import bp as books_bp
from routers.loans import bp as loans_bp
from routers.members import bp as members_bp

app = Flask(__name__)


@app.errorhandler(LibraryError)
def handle_library_error(error):
    return jsonify({"error": error.message}), error.status


app.register_blueprint(books_bp)
app.register_blueprint(members_bp)
app.register_blueprint(loans_bp)


@app.route("/reports/overdue", methods=["GET"])
def report_overdue():
    return jsonify(report_service.overdue_report())


@app.route("/reports/summary", methods=["GET"])
def report_summary():
    return jsonify(report_service.summary_report())


if not os.path.exists("library.db"):
    init_db()
