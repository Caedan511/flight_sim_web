from werkzeug.security import check_password_hash

from backend.db import get_connection


def authenticate_user(username, password):
    """
    Validate a user's login credentials.
    Returns (True, user) on success.
    Returns (False, reason) on failure.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
            SELECT id, uid, username, password_hash, role, status, last_login_at
            FROM users
            WHERE username = %s
            """, (username,))

            user = cursor.fetchone()

            if user is None:
                return False, "Invalid username or password"

            if user["status"] != "active":
                return False, "Account is disabled"

            if not check_password_hash(user["password_hash"], password):
                return False, "Invalid username or password"

            cursor.execute("SELECT NOW() AS current_login_at")
            current_login_at = cursor.fetchone()["current_login_at"]
            cursor.execute("""
            UPDATE users
            SET last_login_at = %s,
                updated_at = updated_at
            WHERE id = %s
            """, (current_login_at, user["id"]))
            conn.commit()

            return True, {
                "id": user["id"],
                "uid": user["uid"],
                "username": user["username"],
                "role": user["role"],
                "status": user["status"],
                "last_login_at": current_login_at,
            }

    finally:
        conn.close()
