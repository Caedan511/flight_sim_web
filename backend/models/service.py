from pathlib import Path

from pymysql.err import IntegrityError

from backend.core.config import Config
from backend.db import get_connection
from backend.users.uid import normalize_user_uid


def _normalize_version(version):
    return version.strip()


def _normalize_name(name):
    return name.strip()


def _safe_filename(filename):
    return Path(filename or "").name


def _safe_version_directory(version):
    safe = "".join(char if char.isalnum() or char in "._-" else "_" for char in version)
    return safe or "model"


def _validate_upload(original_filename):
    filename = _safe_filename(original_filename)
    suffix = Path(filename).suffix.lower()

    if not filename:
        return False, "Model file is required"

    if suffix not in Config.MODEL_ALLOWED_EXTENSIONS:
        return False, "Invalid model file type"

    return True, filename


def _model_storage_path(version, filename):
    return Path("models") / _safe_version_directory(version) / filename


def _model_absolute_path(storage_path):
    return Config.DATA_ROOT / storage_path


def _model_db_path(absolute_path):
    try:
        return str(absolute_path.relative_to(Config.PROJECT_ROOT))
    except ValueError:
        return str(absolute_path)


def _resolve_model_file_path(model_path):
    path = Path(model_path)
    if not path.is_absolute():
        path = Config.PROJECT_ROOT / path
    return path.resolve()


def _write_upload_file(upload_file, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    total_bytes = 0

    with destination.open("wb") as output:
        while True:
            chunk = upload_file.file.read(1024 * 1024)
            if not chunk:
                break

            total_bytes += len(chunk)
            if total_bytes > Config.MODEL_MAX_UPLOAD_BYTES:
                raise ValueError("Model file is too large")

            output.write(chunk)


def _remove_file_if_exists(path):
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


def public_model_version(model):
    if model is None:
        return None

    return {
        "version": model["version"],
        "model_name": model["model_name"],
        "description": model.get("description"),
        "status": model["status"],
        "access_scope": model["access_scope"],
        "created_by_uid": model.get("created_by_uid"),
        "created_by_username": model.get("created_by_username"),
        "created_at": model.get("created_at"),
        "updated_at": model.get("updated_at"),
    }


def public_model_versions(models):
    return [public_model_version(model) for model in models]


def public_model_permission(permission):
    if permission is None:
        return None

    return {
        "model_version": permission["model_version"],
        "user_uid": permission["user_uid"],
        "username": permission["username"],
        "role": permission["role"],
        "user_status": permission["user_status"],
        "can_use": bool(permission["can_use"]),
        "granted_by_uid": permission.get("granted_by_uid"),
        "granted_by_username": permission.get("granted_by_username"),
        "created_at": permission.get("created_at"),
        "updated_at": permission.get("updated_at"),
    }


def public_model_permissions(permissions):
    return [public_model_permission(permission) for permission in permissions]


def _get_model_version_id(cursor, version):
    cursor.execute("""
    SELECT id
    FROM model_versions
    WHERE version = %s
    """, (version,))
    model = cursor.fetchone()
    return model["id"] if model is not None else None


def _get_user_id_by_uid(cursor, uid):
    cursor.execute("""
    SELECT id
    FROM users
    WHERE uid = %s
    """, (uid,))
    user = cursor.fetchone()
    return user["id"] if user is not None else None


def create_model_version(version, model_name, upload_file, description=None, access_scope="private", created_by=None):
    version = _normalize_version(version)
    model_name = _normalize_name(model_name)

    if not version:
        return False, "Model version cannot be empty"
    if not model_name:
        return False, "Model name cannot be empty"
    if access_scope not in ("private", "all_users"):
        return False, "Invalid model access scope"

    valid, result = _validate_upload(upload_file.filename)
    if not valid:
        return False, result

    filename = result
    storage_path = _model_storage_path(version, filename)
    saved_path = _model_absolute_path(storage_path)

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            if created_by is not None:
                cursor.execute("SELECT id FROM users WHERE id = %s", (created_by,))
                if cursor.fetchone() is None:
                    return False, "Creator user does not exist"

            if _get_model_version_id(cursor, version) is not None:
                return False, "Model version already exists"

            _write_upload_file(upload_file, saved_path)

            cursor.execute("""
            INSERT INTO model_versions (
                version,
                model_name,
                model_path,
                description,
                access_scope,
                created_by
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            """, (version, model_name, _model_db_path(saved_path), description, access_scope, created_by))

        conn.commit()
        return True, "Model version created successfully"

    except IntegrityError:
        conn.rollback()
        _remove_file_if_exists(saved_path)
        return False, "Model version already exists"

    except ValueError as e:
        conn.rollback()
        _remove_file_if_exists(saved_path)
        return False, str(e)

    except Exception as e:
        conn.rollback()
        _remove_file_if_exists(saved_path)
        return False, f"Failed to create model version: {e}"

    finally:
        conn.close()
        upload_file.file.close()


def list_model_versions(include_disabled=True):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            status_filter = "" if include_disabled else "WHERE mv.status = 'active'"
            cursor.execute(f"""
            SELECT
                mv.version,
                mv.model_name,
                mv.description,
                mv.status,
                mv.access_scope,
                creator.uid AS created_by_uid,
                creator.username AS created_by_username,
                mv.created_at,
                mv.updated_at
            FROM model_versions mv
            LEFT JOIN users creator
                ON creator.id = mv.created_by
            {status_filter}
            ORDER BY mv.created_at DESC
            """)
            return cursor.fetchall()

    finally:
        conn.close()


def update_model_version(
    current_version,
    version=None,
    model_name=None,
    description=None,
    status=None,
    access_scope=None
):
    current_version = _normalize_version(current_version)
    if not current_version:
        return False, "Model version does not exist"

    if status is not None and status not in ("active", "disabled"):
        return False, "Invalid model status"
    if access_scope is not None and access_scope not in ("private", "all_users"):
        return False, "Invalid model access scope"

    updates = {
        "version": _normalize_version(version) if version is not None else None,
        "model_name": _normalize_name(model_name) if model_name is not None else None,
        "description": description,
        "status": status,
        "access_scope": access_scope,
    }
    fields = []
    values = []

    for field, value in updates.items():
        if value is not None:
            if field == "version" and not value:
                return False, "Model version cannot be empty"
            if field == "model_name" and not value:
                return False, "Model name cannot be empty"
            fields.append(f"{field} = %s")
            values.append(value)

    if not fields:
        return False, "No model version fields to update"

    values.append(current_version)

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
            SELECT id
            FROM model_versions
            WHERE version = %s
            """, (current_version,))
            if cursor.fetchone() is None:
                return False, "Model version does not exist"

            cursor.execute(f"""
            UPDATE model_versions
            SET {", ".join(fields)}
            WHERE version = %s
            """, values)

        conn.commit()
        return True, "Model version updated successfully"

    except IntegrityError:
        conn.rollback()
        return False, "Model version already exists"

    except Exception as e:
        conn.rollback()
        return False, f"Failed to update model version: {e}"

    finally:
        conn.close()


def list_model_version_permissions(version):
    version = _normalize_version(version)
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
            SELECT
                mv.version AS model_version,
                u.uid AS user_uid,
                u.username,
                u.role,
                u.status AS user_status,
                mvp.can_use,
                grantor.uid AS granted_by_uid,
                grantor.username AS granted_by_username,
                mvp.created_at,
                mvp.updated_at
            FROM model_version_permissions mvp
            JOIN model_versions mv
                ON mv.id = mvp.model_version_id
            JOIN users u
                ON u.id = mvp.user_id
            LEFT JOIN users grantor
                ON grantor.id = mvp.granted_by
            WHERE mv.version = %s
            ORDER BY u.username ASC
            """, (version,))
            return cursor.fetchall()

    finally:
        conn.close()


def grant_model_version_access(version, user_uid, granted_by=None):
    version = _normalize_version(version)
    user_uid = normalize_user_uid(user_uid)
    if not version:
        return False, "Model version does not exist"
    if not user_uid:
        return False, "User does not exist"

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            model_version_id = _get_model_version_id(cursor, version)
            if model_version_id is None:
                return False, "Model version does not exist"

            user_id = _get_user_id_by_uid(cursor, user_uid)
            if user_id is None:
                return False, "User does not exist"

            if granted_by is not None:
                cursor.execute("SELECT id FROM users WHERE id = %s", (granted_by,))
                if cursor.fetchone() is None:
                    return False, "Granting user does not exist"

            cursor.execute("""
            INSERT INTO model_version_permissions (
                model_version_id,
                user_id,
                can_use,
                granted_by
            )
            VALUES (%s, %s, 1, %s)
            ON DUPLICATE KEY UPDATE
                can_use = VALUES(can_use),
                granted_by = VALUES(granted_by)
            """, (model_version_id, user_id, granted_by))

        conn.commit()
        return True, "Model version access granted successfully"

    except Exception as e:
        conn.rollback()
        return False, f"Failed to grant model version access: {e}"

    finally:
        conn.close()


def revoke_model_version_access(version, user_uid):
    version = _normalize_version(version)
    user_uid = normalize_user_uid(user_uid)
    if not version:
        return False, "Model version does not exist"
    if not user_uid:
        return False, "User does not exist"

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            model_version_id = _get_model_version_id(cursor, version)
            if model_version_id is None:
                return False, "Model version does not exist"

            user_id = _get_user_id_by_uid(cursor, user_uid)
            if user_id is None:
                return False, "User does not exist"

            cursor.execute("""
            UPDATE model_version_permissions
            SET can_use = 0
            WHERE model_version_id = %s AND user_id = %s
            """, (model_version_id, user_id))

            if cursor.rowcount == 0:
                return True, "Model version access is already revoked"

        conn.commit()
        return True, "Model version access revoked successfully"

    except Exception as e:
        conn.rollback()
        return False, f"Failed to revoke model version access: {e}"

    finally:
        conn.close()


def can_user_use_model_version(user, version):
    if user is None or user["status"] != "active":
        return False
    if user["role"] == "admin":
        return True

    version = _normalize_version(version)
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
            SELECT 1
            FROM model_versions mv
            LEFT JOIN model_version_permissions mvp
                ON mvp.model_version_id = mv.id
                AND mvp.user_id = %s
                AND mvp.can_use = 1
            WHERE mv.version = %s
                AND mv.status = 'active'
                AND (mv.access_scope = 'all_users' OR mvp.id IS NOT NULL)
            LIMIT 1
            """, (user["id"], version))

            return cursor.fetchone() is not None

    finally:
        conn.close()


def get_model_version_for_simulation(user, version):
    if user is None or user["status"] != "active":
        return None

    version = _normalize_version(version)
    if not version:
        return None

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            if user["role"] == "admin":
                cursor.execute("""
                SELECT version, model_name, model_path, status, access_scope
                FROM model_versions
                WHERE version = %s
                    AND status = 'active'
                LIMIT 1
                """, (version,))
            else:
                cursor.execute("""
                SELECT mv.version, mv.model_name, mv.model_path, mv.status, mv.access_scope
                FROM model_versions mv
                LEFT JOIN model_version_permissions mvp
                    ON mvp.model_version_id = mv.id
                    AND mvp.user_id = %s
                    AND mvp.can_use = 1
                WHERE mv.version = %s
                    AND mv.status = 'active'
                    AND (mv.access_scope = 'all_users' OR mvp.id IS NOT NULL)
                LIMIT 1
                """, (user["id"], version))

            model = cursor.fetchone()
            if model is None:
                return None

            model["model_path"] = str(_resolve_model_file_path(model["model_path"]))
            return model

    finally:
        conn.close()


def list_accessible_model_versions(user):
    if user is None or user["status"] != "active":
        return []

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            if user["role"] == "admin":
                cursor.execute("""
                SELECT
                    mv.version,
                    mv.model_name,
                    mv.description,
                    mv.status,
                    mv.access_scope,
                    creator.uid AS created_by_uid,
                    creator.username AS created_by_username,
                    mv.created_at,
                    mv.updated_at
                FROM model_versions mv
                LEFT JOIN users creator
                    ON creator.id = mv.created_by
                WHERE mv.status = 'active'
                ORDER BY mv.created_at DESC
                """)
                return cursor.fetchall()

            cursor.execute("""
            SELECT DISTINCT
                mv.version,
                mv.model_name,
                mv.description,
                mv.status,
                mv.access_scope,
                creator.uid AS created_by_uid,
                creator.username AS created_by_username,
                mv.created_at,
                mv.updated_at
            FROM model_versions mv
            LEFT JOIN model_version_permissions mvp
                ON mvp.model_version_id = mv.id
                AND mvp.user_id = %s
                AND mvp.can_use = 1
            LEFT JOIN users creator
                ON creator.id = mv.created_by
            WHERE mv.status = 'active'
                AND (mv.access_scope = 'all_users' OR mvp.id IS NOT NULL)
            ORDER BY mv.created_at DESC
            """, (user["id"],))

            return cursor.fetchall()

    finally:
        conn.close()
