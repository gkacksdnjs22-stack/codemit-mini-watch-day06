from db import connect_db


def find_user(username):
    with connect_db() as conn:
        return conn.execute(
            "SELECT id, username, display_name, password_hash FROM users WHERE username = %s",
            (username,),
        ).fetchone()


def find_user_by_id(user_id):
    with connect_db() as conn:
        return conn.execute("SELECT id, username, display_name FROM users WHERE id = %s", (user_id,)).fetchone()


def create_user(username, display_name, password_hash):
    with connect_db() as conn:
        return conn.execute(
            "INSERT INTO users (username, display_name, password_hash) VALUES (%s, %s, %s) RETURNING id",
            (username, display_name, password_hash),
        ).fetchone()

