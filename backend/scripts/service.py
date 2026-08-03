from pathlib import Path
from pymysql.err import IntegrityError

from backend.core.config import Config
from backend.db import get_connection
from backend.scripts.code import (
    format_script_code,
    make_pending_script_code,
    normalize_script_code,
)


def _normalize_name(name):
    return name.strip()


def public_script(script):
    if script is None:
        return None

    return {
        "script_code": script["script_code"],
        "name": script["name"],
        "original_filename": script["original_filename"],
        "scope": script["scope"],
        "status": script["status"],
        "description": script.get("description"),
        "created_at": script.get("created_at"),
        "updated_at": script.get("updated_at"),
    }


def public_scripts(scripts):
    return [public_script(script) for script in scripts]


def _safe_filename(filename):
    return Path(filename or "").name


def _validate_upload(original_filename):
    filename = _safe_filename(original_filename)
    suffix = Path(filename).suffix.lower()

    if not filename:
        return False, "Script file is required"

    if suffix not in Config.SCRIPT_ALLOWED_EXTENSIONS:
        return False, "Invalid script file type"

    return True, filename


def _script_storage_path(script_code, suffix, scope, owner_user_uid=None):
    filename = f"{script_code}{suffix}"
    if scope == "public":
        return Path("public") / "scripts" / filename

    return Path("users") / owner_user_uid / "scripts" / filename


def _script_absolute_path(storage_path):
    return Config.DATA_ROOT / storage_path


def _script_db_path(absolute_path):
    try:
        return str(absolute_path.relative_to(Config.PROJECT_ROOT))
    except ValueError:
        return str(absolute_path)


def _write_upload_file(upload_file, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    total_bytes = 0

    with destination.open("wb") as output:
        while True:
            chunk = upload_file.file.read(1024 * 1024)
            if not chunk:
                break

            total_bytes += len(chunk)
            if total_bytes > Config.SCRIPT_MAX_UPLOAD_BYTES:
                raise ValueError("Script file is too large")

            output.write(chunk)


def _remove_file_if_exists(path):
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


def create_script(upload_file, name, description, scope, owner_user):
    name = _normalize_name(name)
    if not name:
        return False, "Script name cannot be empty", None

    if scope not in ("private", "public"):
        return False, "Invalid script scope", None

    if scope == "private" and owner_user is None:
        return False, "Script owner is required", None

    valid, result = _validate_upload(upload_file.filename)
    if not valid:
        return False, result, None

    original_filename = result
    suffix = Path(original_filename).suffix.lower()
    owner_user_id = owner_user["id"] if owner_user is not None else None
    owner_user_uid = owner_user["uid"] if owner_user is not None else None
    pending_code = make_pending_script_code()
    pending_path = str(Path("data") / "_pending" / pending_code)
    saved_path = None

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
            INSERT INTO flight_scripts (
                script_code,
                owner_user_id,
                name,
                original_filename,
                file_path,
                scope,
                status,
                description
            )
            VALUES (%s, %s, %s, %s, %s, %s, 'active', %s)
            """, (
                pending_code,
                owner_user_id,
                name,
                original_filename,
                pending_path,
                scope,
                description,
            ))

            script_id = cursor.lastrowid
            script_code = format_script_code(script_id)
            storage_path = _script_storage_path(
                script_code,
                suffix,
                scope,
                owner_user_uid,
            )
            saved_path = _script_absolute_path(storage_path)
            _write_upload_file(upload_file, saved_path)

            cursor.execute("""
            UPDATE flight_scripts
            SET script_code = %s,
                file_path = %s
            WHERE id = %s
            """, (script_code, _script_db_path(saved_path), script_id))

            cursor.execute("""
            SELECT id, script_code, owner_user_id, name, original_filename,
                file_path, scope, status, description, created_at, updated_at
            FROM flight_scripts
            WHERE id = %s
            """, (script_id,))
            script = cursor.fetchone()

        conn.commit()
        return True, "Script uploaded successfully", script

    except IntegrityError:
        conn.rollback()
        if saved_path is not None:
            _remove_file_if_exists(saved_path)
        return False, "Script code already exists", None

    except ValueError as e:
        conn.rollback()
        if saved_path is not None:
            _remove_file_if_exists(saved_path)
        return False, str(e), None

    except Exception as e:
        conn.rollback()
        if saved_path is not None:
            _remove_file_if_exists(saved_path)
        return False, f"Failed to upload script: {e}", None

    finally:
        conn.close()
        upload_file.file.close()


def list_accessible_scripts(user_id):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
            SELECT id, script_code, owner_user_id, name, original_filename,
                file_path, scope, status, description, created_at, updated_at
            FROM flight_scripts
            WHERE status = 'active'
                AND (scope = 'public' OR owner_user_id = %s)
            ORDER BY created_at DESC
            """, (user_id,))
            return cursor.fetchall()

    finally:
        conn.close()


def list_all_scripts(include_deleted=False):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            if include_deleted:
                cursor.execute("""
                SELECT id, script_code, owner_user_id, name, original_filename,
                    file_path, scope, status, description, created_at, updated_at
                FROM flight_scripts
                ORDER BY created_at DESC
                """)
            else:
                cursor.execute("""
                SELECT id, script_code, owner_user_id, name, original_filename,
                    file_path, scope, status, description, created_at, updated_at
                FROM flight_scripts
                WHERE status != 'deleted'
                ORDER BY created_at DESC
                """)

            return cursor.fetchall()

    finally:
        conn.close()


def get_accessible_script(script_code, user_id):
    script_code = normalize_script_code(script_code)
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
            SELECT id, script_code, owner_user_id, name, original_filename,
                file_path, scope, status, description, created_at, updated_at
            FROM flight_scripts
            WHERE script_code = %s
                AND status = 'active'
                AND (scope = 'public' OR owner_user_id = %s)
            """, (script_code, user_id))
            return cursor.fetchone()

    finally:
        conn.close()


def get_script_for_admin(script_code):
    script_code = normalize_script_code(script_code)
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
            SELECT id, script_code, owner_user_id, name, original_filename,
                file_path, scope, status, description, created_at, updated_at
            FROM flight_scripts
            WHERE script_code = %s
            """, (script_code,))
            return cursor.fetchone()

    finally:
        conn.close()


def get_script_file_path(script):
    path = Path(script["file_path"])
    if path.is_absolute():
        return path

    return Config.PROJECT_ROOT / path


def soft_delete_script(script_code, user_id):
    script_code = normalize_script_code(script_code)
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
            UPDATE flight_scripts
            SET status = 'deleted'
            WHERE script_code = %s
                AND owner_user_id = %s
                AND scope = 'private'
                AND status != 'deleted'
            """, (script_code, user_id))

            if cursor.rowcount == 0:
                conn.rollback()
                return False, "Script does not exist or cannot be deleted"

        conn.commit()
        return True, "Script deleted successfully"

    except Exception as e:
        conn.rollback()
        return False, f"Failed to delete script: {e}"

    finally:
        conn.close()


def update_script_for_admin(script_code, name=None, description=None, status=None, scope=None):
    script_code = normalize_script_code(script_code)

    if status is not None and status not in ("active", "disabled", "deleted"):
        return False, "Invalid script status"

    if scope is not None and scope not in ("private", "public"):
        return False, "Invalid script scope"

    updates = {
        "name": _normalize_name(name) if name is not None else None,
        "description": description,
        "status": status,
        "scope": scope,
    }
    fields = []
    values = []

    for field, value in updates.items():
        if value is not None:
            if field == "name" and not value:
                return False, "Script name cannot be empty"
            fields.append(f"{field} = %s")
            values.append(value)

    if not fields:
        return False, "No script fields to update"

    values.append(script_code)

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(f"""
            UPDATE flight_scripts
            SET {", ".join(fields)}
            WHERE script_code = %s
            """, values)

            if cursor.rowcount == 0:
                conn.rollback()
                return False, "Script does not exist"

        conn.commit()
        return True, "Script updated successfully"

    except Exception as e:
        conn.rollback()
        return False, f"Failed to update script: {e}"

    finally:
        conn.close()
