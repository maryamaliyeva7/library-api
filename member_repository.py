import db


def list_members():
    conn = db.connect()
    rows = conn.execute("SELECT * FROM members").fetchall()
    conn.close()
    return rows


def get_member(member_id):
    conn = db.connect()
    member = conn.execute("SELECT * FROM members WHERE id = ?", (member_id,)).fetchone()
    conn.close()
    return member


def get_member_by_email(email):
    conn = db.connect()
    member = conn.execute("SELECT * FROM members WHERE email = ?", (email,)).fetchone()
    conn.close()
    return member


def create_member(name, email, member_type):
    conn = db.connect()
    cur = conn.execute(
        "INSERT INTO members (name, email, type) VALUES (?, ?, ?)",
        (name, email, member_type),
    )
    conn.commit()
    member = conn.execute("SELECT * FROM members WHERE id = ?", (cur.lastrowid,)).fetchone()
    conn.close()
    return member
