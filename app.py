import os

from flask import Flask, jsonify

import book_routes
import loan_routes
import member_routes
import report_routes
from db import init_db
from errors import LibraryError

app = Flask(__name__)
app.register_blueprint(book_routes.bp)
app.register_blueprint(member_routes.bp)
app.register_blueprint(loan_routes.bp)
app.register_blueprint(report_routes.bp)


@app.errorhandler(LibraryError)
def handle_library_error(error):
    return jsonify({"error": error.message}), error.status


if not os.path.exists("library.db"):
    init_db()
