from werkzeug.security import check_password_hash, generate_password_hash
from pymysql.err import IntegrityError

from backend.db import get_connection
from backend.users.uid import format_user_uid, make_pending_user_uid, normalize_user_uid


def _normalize_username(username):
    return username.strip()


def public_user(user):
    if user is None:
        return None

    return {
        "uid": user["uid"],
        "username": user["username"],
        "role": user["role"],
        "status": user["status"],
        "last_login_at": user.get("last_login_at"),
        "created_at": user.get("created_at"),
        "updated_at": user.get("updated_at"),
    }


def public_users(users):
    return [public_user(user) for user in users]


def create_user(username, password, role="normal"):
    """
    Create a normal or admin user.
    """
    username = _normalize_username(username)
    if not username:
        return False, "Username cannot be empty"

    if role not in ("admin", "normal"):
        return False, "Invalid user role"

    password_hash = generate_password_hash(password)

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
            SELECT id
            FROM users
            WHERE username = %s
            """, (username,))
            if cursor.fetchone() is not None:
                return False, "Username already exists"

            pending_uid = make_pending_user_uid()
            cursor.execute("""
            INSERT INTO users (uid, username, password_hash, role, status)
            VALUES (%s, %s, %s, %s, %s)
            """, (pending_uid, username, password_hash, role, "active"))

            user_id = cursor.lastrowid
            cursor.execute("""
            UPDATE users
            SET uid = %s
            WHERE id = %s
            """, (format_user_uid(user_id), user_id))

        conn.commit()
        return True, "User created successfully"

    except IntegrityError:
        conn.rollback()
        return False, "Username already exists"

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
            SELECT id, uid, username, role, status, last_login_at, created_at, updated_at
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
            SELECT id, uid, username, role, status, last_login_at, created_at, updated_at
            FROM users
            WHERE id = %s
            """, (user_id,))
            return cursor.fetchone()

    finally:
        conn.close()


def get_user_by_username(username):
    username = _normalize_username(username)
    if not username:
        return None

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
            SELECT id, uid, username, role, status, last_login_at, created_at, updated_at
            FROM users
            WHERE username = %s
            """, (username,))
            return cursor.fetchone()

    finally:
        conn.close()


def get_user_by_uid(uid):
    uid = normalize_user_uid(uid)
    if not uid:
        return None

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
            SELECT id, uid, username, role, status, last_login_at, created_at, updated_at
            FROM users
            WHERE uid = %s
            """, (uid,))
            return cursor.fetchone()

    finally:
        conn.close()


def update_user_role(uid, role):
    uid = normalize_user_uid(uid)
    if not uid:
        return False, "User does not exist"

    if role not in ("admin", "normal"):
        return False, "Invalid user role"

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
            SELECT role
            FROM users
            WHERE uid = %s
            """, (uid,))
            user = cursor.fetchone()

            if user is None:
                return False, "User does not exist"

            if user["role"] == role:
                return True, "User role is already up to date"

            cursor.execute("""
            UPDATE users
            SET role = %s
            WHERE uid = %s
            """, (role, uid))

        conn.commit()
        return True, "User role updated successfully"

    except Exception as e:
        conn.rollback()
        return False, f"Failed to update user role: {e}"

    finally:
        conn.close()


def update_user_status(uid, status):
    uid = normalize_user_uid(uid)
    if not uid:
        return False, "User does not exist"
    
    if status not in ("active", "disabled"):
        return False, "Invalid user status"

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
            SELECT status
            FROM users
            WHERE uid = %s
            """, (uid,))
            user = cursor.fetchone()

            if user is None:
                return False, "User does not exist"

            if user["status"] == status:
                return True, "User status is already up to date"

            cursor.execute("""
            UPDATE users
            SET status = %s
            WHERE uid = %s
            """, (status, uid))

        conn.commit()
        return True, "User status updated successfully"

    except Exception as e:
        conn.rollback()
        return False, f"Failed to update user status: {e}"

    finally:
        conn.close()


def change_password(user_id, old_password, new_password):
    if old_password == new_password:
        return False, "New password must be different from old password"

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
            SELECT id, password_hash, status
            FROM users
            WHERE id = %s
            """, (user_id,))
            user = cursor.fetchone()

            if user is None:
                return False, "User does not exist"

            if user["status"] != "active":
                return False, "Account is disabled"

            if not check_password_hash(user["password_hash"], old_password):
                return False, "Old password is incorrect"

            password_hash = generate_password_hash(new_password)
            cursor.execute("""
            UPDATE users
            SET password_hash = %s
            WHERE id = %s
            """, (password_hash, user_id))

        conn.commit()
        return True, "Password changed successfully"

    except Exception as e:
        conn.rollback()
        return False, f"Failed to change password: {e}"

    finally:
        conn.close()


def reset_password_by_uid(uid, new_password):
    uid = normalize_user_uid(uid)
    if not uid:
        return False, "User does not exist"

    password_hash = generate_password_hash(new_password)

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
            UPDATE users
            SET password_hash = %s
            WHERE uid = %s
            """, (password_hash, uid))

            if cursor.rowcount == 0:
                conn.rollback()
                return False, "User does not exist"

        conn.commit()
        return True, "User password reset successfully"

    except Exception as e:
        conn.rollback()
        return False, f"Failed to reset user password: {e}"

    finally:
        conn.close()
