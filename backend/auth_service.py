from werkzeug.security import check_password_hash, generate_password_hash
from backend.db import get_connection


def authenticate_user(username, password):
    """
    Validate a user's login credentials.
    Returns (True, role) on success.
    Returns (False, reason) on failure.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
            SELECT username, password_hash, role, status
            FROM users
            WHERE username = %s
            """, (username,))

            user = cursor.fetchone()

            if user is None:
                return False, "User does not exist"

            if user["status"] != "active":
                return False, "Account is disabled"

            if not check_password_hash(user["password_hash"], password):
                return False, "Incorrect password"

            return True, user["role"]

    finally:
        conn.close()


def create_user(username, password, role="normal"):
    """
    Create a normal or admin user.
    """
    if role not in ("admin", "normal"):
        return False, "Invalid user role"

    password_hash = generate_password_hash(password)

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
            INSERT INTO users (username, password_hash, role, status)
            VALUES (%s, %s, %s, %s)
            """, (username, password_hash, role, "active"))

        conn.commit()
        return True, "User created successfully"

    except Exception as e:
        conn.rollback()
        return False, f"Failed to create user: {e}"

    finally:
        conn.close()


def list_users():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
            SELECT id, username, role, status, created_at, updated_at
            FROM users
            ORDER BY id ASC
            """)
            return cursor.fetchall()

    finally:
        conn.close()


def get_user_by_id(user_id):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
            SELECT id, username, role, status, created_at, updated_at
            FROM users
            WHERE id = %s
            """, (user_id,))
            return cursor.fetchone()

    finally:
        conn.close()


def update_user_role(user_id, role):
    if role not in ("admin", "normal"):
        return False, "Invalid user role"

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
            UPDATE users
            SET role = %s
            WHERE id = %s
            """, (role, user_id))

            if cursor.rowcount == 0:
                conn.rollback()
                return False, "User does not exist"

        conn.commit()
        return True, "User role updated successfully"

    except Exception as e:
        conn.rollback()
        return False, f"Failed to update user role: {e}"

    finally:
        conn.close()


def update_user_status(user_id, status):
    if status not in ("active", "disabled"):
        return False, "Invalid user status"

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
            UPDATE users
            SET status = %s
            WHERE id = %s
            """, (status, user_id))

            if cursor.rowcount == 0:
                conn.rollback()
                return False, "User does not exist"

        conn.commit()
        return True, "User status updated successfully"

    except Exception as e:
        conn.rollback()
        return False, f"Failed to update user status: {e}"

    finally:
        conn.close()
