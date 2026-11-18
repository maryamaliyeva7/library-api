import db


def list_books(only_available):
    conn = db.connect()
    if only_available:
        rows = conn.execute("SELECT * FROM books WHERE available = 1").fetchall()
    else:
        rows = conn.execute("SELECT * FROM books").fetchall()
    conn.close()
    return rows


def get_book(book_id):
    conn = db.connect()
    book = conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
    conn.close()
    return book


def create_book(title, author, isbn):
    conn = db.connect()
    cur = conn.execute(
        "INSERT INTO books (title, author, isbn, available) VALUES (?, ?, ?, 1)",
        (title, author, isbn),
    )
    conn.commit()
    book = conn.execute("SELECT * FROM books WHERE id = ?", (cur.lastrowid,)).fetchone()
    conn.close()
    return book


def delete_book(book_id):
    conn = db.connect()
    conn.execute("DELETE FROM books WHERE id = ?", (book_id,))
    conn.commit()
    conn.close()


def count_books():
    conn = db.connect()
    total = conn.execute("SELECT COUNT(*) FROM books").fetchone()[0]
    conn.close()
    return total


def set_availability(book_id, available):
    conn = db.connect()
    conn.execute("UPDATE books SET available = ? WHERE id = ?", (int(available), book_id))
    conn.commit()
    conn.close()
