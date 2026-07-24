from backend.db import get_connection


def create_model_version(
    version,
    model_name,
    model_path,
    description=None,
    access_scope="private",
    created_by=None
):
    if access_scope not in ("private", "all_users"):
        return False, "Invalid model access scope"

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            if created_by is not None:
                cursor.execute("SELECT id FROM users WHERE id = %s", (created_by,))
                if cursor.fetchone() is None:
                    return False, "Creator user does not exist"

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
            """, (version, model_name, model_path, description, access_scope, created_by))

        conn.commit()
        return True, "Model version created successfully"

    except Exception as e:
        conn.rollback()
        return False, f"Failed to create model version: {e}"

    finally:
        conn.close()


def list_model_versions(include_disabled=True):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            if include_disabled:
                cursor.execute("""
                SELECT id, version, model_name, model_path, description,
                    status, access_scope, created_by, created_at, updated_at
                FROM model_versions
                ORDER BY created_at DESC
                """)
            else:
                cursor.execute("""
                SELECT id, version, model_name, model_path, description,
                    status, access_scope, created_by, created_at, updated_at
                FROM model_versions
                WHERE status = 'active'
                ORDER BY created_at DESC
                """)

            return cursor.fetchall()

    finally:
        conn.close()


def update_model_version(
    model_version_id,
    version=None,
    model_name=None,
    model_path=None,
    description=None,
    status=None,
    access_scope=None
):
    if status is not None and status not in ("active", "disabled"):
        return False, "Invalid model status"

    if access_scope is not None and access_scope not in ("private", "all_users"):
        return False, "Invalid model access scope"

    fields = []
    values = []
    update_values = {
        "version": version,
        "model_name": model_name,
        "model_path": model_path,
        "description": description,
        "status": status,
        "access_scope": access_scope,
    }

    for field, value in update_values.items():
        if value is not None:
            fields.append(f"{field} = %s")
            values.append(value)

    if not fields:
        return False, "No model version fields to update"

    values.append(model_version_id)

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(f"""
            UPDATE model_versions
            SET {", ".join(fields)}
            WHERE id = %s
            """, values)

            if cursor.rowcount == 0:
                conn.rollback()
                return False, "Model version does not exist"

        conn.commit()
        return True, "Model version updated successfully"

    except Exception as e:
        conn.rollback()
        return False, f"Failed to update model version: {e}"

    finally:
        conn.close()


def grant_model_version_access(model_version_id, user_id, granted_by=None):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM model_versions WHERE id = %s", (model_version_id,))
            if cursor.fetchone() is None:
                return False, "Model version does not exist"

            cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
            if cursor.fetchone() is None:
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


def revoke_model_version_access(model_version_id, user_id):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
            UPDATE model_version_permissions
            SET can_use = 0
            WHERE model_version_id = %s AND user_id = %s
            """, (model_version_id, user_id))

        conn.commit()
        return True, "Model version access revoked successfully"

    except Exception as e:
        conn.rollback()
        return False, f"Failed to revoke model version access: {e}"

    finally:
        conn.close()


def list_model_version_permissions(model_version_id):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
            SELECT
                mvp.id,
                mvp.model_version_id,
                mvp.user_id,
                u.username,
                u.role,
                u.status AS user_status,
                mvp.can_use,
                mvp.granted_by,
                mvp.created_at,
                mvp.updated_at
            FROM model_version_permissions mvp
            JOIN users u
                ON u.id = mvp.user_id
            WHERE mvp.model_version_id = %s
            ORDER BY u.username ASC
            """, (model_version_id,))
            return cursor.fetchall()

    finally:
        conn.close()


def can_user_use_model_version(username, version):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
            SELECT u.role
            FROM users u
            WHERE u.username = %s AND u.status = 'active'
            """, (username,))
            user = cursor.fetchone()

            if user is None:
                return False

            if user["role"] == "admin":
                return True

            cursor.execute("""
            SELECT 1
            FROM model_versions mv
            LEFT JOIN model_version_permissions mvp
                ON mvp.model_version_id = mv.id
                AND mvp.user_id = (
                    SELECT id FROM users WHERE username = %s
                )
                AND mvp.can_use = 1
            WHERE mv.version = %s
                AND mv.status = 'active'
                AND (mv.access_scope = 'all_users' OR mvp.id IS NOT NULL)
            LIMIT 1
            """, (username, version))

            return cursor.fetchone() is not None

    finally:
        conn.close()


def list_accessible_model_versions(username):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
            SELECT id, role
            FROM users
            WHERE username = %s AND status = 'active'
            """, (username,))
            user = cursor.fetchone()

            if user is None:
                return []

            if user["role"] == "admin":
                cursor.execute("""
                SELECT id, version, model_name, model_path, description, status, access_scope
                FROM model_versions
                WHERE status = 'active'
                ORDER BY created_at DESC
                """)
                return cursor.fetchall()

            cursor.execute("""
            SELECT DISTINCT
                mv.id,
                mv.version,
                mv.model_name,
                mv.model_path,
                mv.description,
                mv.status,
                mv.access_scope
            FROM model_versions mv
            LEFT JOIN model_version_permissions mvp
                ON mvp.model_version_id = mv.id
                AND mvp.user_id = %s
                AND mvp.can_use = 1
            WHERE mv.status = 'active'
                AND (mv.access_scope = 'all_users' OR mvp.id IS NOT NULL)
            ORDER BY mv.created_at DESC
            """, (user["id"],))

            return cursor.fetchall()

    finally:
        conn.close()
