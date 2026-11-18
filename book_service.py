import book_repository
import validation
from errors import bad_request, conflict, not_found


def list_books(only_available):
    return book_repository.list_books(only_available)


def get_book(book_id):
    book = book_repository.get_book(book_id)
    if book is None:
        raise not_found("book not found")
    return book


def create_book(data):
    if not data.get("title") or not data.get("author"):
        raise bad_request("title and author are required")
    if not validation.is_valid_isbn(data.get("isbn")):
        raise bad_request("invalid isbn")
    return book_repository.create_book(data["title"], data["author"], data["isbn"])


def delete_book(book_id):
    book = get_book(book_id)
    if book["available"] == 0:
        raise conflict("book is on loan")
    book_repository.delete_book(book_id)