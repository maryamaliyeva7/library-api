from flask import Blueprint, jsonify, request

import book_service

bp = Blueprint("books", __name__)


def book_json(book):
    return {
        "id": book["id"],
        "title": book["title"],
        "author": book["author"],
        "isbn": book["isbn"],
        "available": bool(book["available"]),
    }


@bp.route("/books", methods=["GET"])
def list_books():
    only_available = request.args.get("available") == "true"
    return jsonify([book_json(book) for book in book_service.list_books(only_available)])


@bp.route("/books/<int:book_id>", methods=["GET"])
def get_book(book_id):
    return jsonify(book_json(book_service.get_book(book_id)))


@bp.route("/books", methods=["POST"])
def create_book():
    data = request.get_json(silent=True) or {}
    return jsonify(book_json(book_service.create_book(data))), 201


@bp.route("/books/<int:book_id>", methods=["DELETE"])
def delete_book(book_id):
    book_service.delete_book(book_id)
    return "", 204
