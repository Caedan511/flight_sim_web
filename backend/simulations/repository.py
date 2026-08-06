import json

from backend.core.config import Config
from backend.db import get_connection
from backend.simulations.code import format_task_code, make_pending_task_code, normalize_task_code
from backend.simulations.contracts import TaskRecord


def _json_dumps(value):
    return json.dumps(value or [], ensure_ascii=False)


def _json_loads(value):
    if not value:
        return []
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return []


def _artifact_public_rows(task_code):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
            SELECT artifact_code, task_code, artifact_type, filename, file_path, content_type
            FROM simulation_artifacts
            WHERE task_code = %s
            ORDER BY id ASC
            """, (task_code,))
            return cursor.fetchall()
    finally:
        conn.close()


def _record_from_row(row, artifacts=None):
    if row is None:
        return None

    return TaskRecord(
        id=row["id"],
        task_code=row["task_code"],
        user_id=row["user_id"],
        user_uid=row["user_uid"],
        script_code=row["script_code"],
        subject=row["subject"],
        model_version=row.get("model_version"),
        model_name=row["model_name"],
        report_template_code=row["report_template_code"],
        output_parameters=_json_loads(row.get("output_parameters_json")),
        output_directory=row["output_directory"],
        status=row["status"],
        progress=row["progress"],
        failed_points=row["failed_points"],
        message=row["message"],
        error_message=row.get("error_message"),
        submitted_at=row.get("submitted_at"),
        started_at=row.get("started_at"),
        finished_at=row.get("finished_at"),
        updated_at=row.get("updated_at"),
        artifacts=artifacts if artifacts is not None else _artifact_public_rows(row["task_code"]),
    )


def create_task(
    *,
    user_id,
    user_uid,
    script_code,
    subject,
    model_version,
    model_name,
    report_template_code,
    output_parameters,
):
    pending_code = make_pending_task_code()
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
            INSERT INTO simulation_tasks (
                task_code, user_id, user_uid, script_code,
                subject, model_version, model_name, report_template_code,
                output_parameters_json, output_directory, status, progress,
                message
            )
            VALUES (
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, 'queued', 0,
                'Simulation task queued'
            )
            """, (
                pending_code,
                user_id,
                user_uid,
                script_code,
                subject,
                model_version,
                model_name,
                report_template_code,
                _json_dumps(output_parameters),
                "",
            ))
            task_id = cursor.lastrowid
            task_code = format_task_code(task_id)
            output_directory = str(
                (Config.DATA_ROOT / "users" / user_uid / "simulations" / task_code).resolve()
            )
            cursor.execute("""
            UPDATE simulation_tasks
            SET task_code = %s,
                output_directory = %s
            WHERE id = %s
            """, (task_code, output_directory, task_id))
            cursor.execute("""
            SELECT *
            FROM simulation_tasks
            WHERE id = %s
            """, (task_id,))
            row = cursor.fetchone()

        conn.commit()
        return _record_from_row(row, [])
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def update_task(task_code, **changes):
    task_code = normalize_task_code(task_code)
    if not changes:
        return get_task(task_code)

    fields = []
    values = []
    allowed = {
        "status",
        "progress",
        "failed_points",
        "message",
        "error_message",
        "started_at",
        "finished_at",
    }
    for field, value in changes.items():
        if field not in allowed:
            raise ValueError(f"Unknown simulation task field: {field}")
        if field in {"started_at", "finished_at"} and value == "NOW":
            fields.append(f"{field} = NOW()")
        else:
            fields.append(f"{field} = %s")
            values.append(value)

    values.append(task_code)
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(f"""
            UPDATE simulation_tasks
            SET {", ".join(fields)}
            WHERE task_code = %s
            """, values)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return get_task(task_code)


def replace_artifacts(task_code, artifacts):
    task_code = normalize_task_code(task_code)
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM simulation_artifacts WHERE task_code = %s", (task_code,))
            for artifact in artifacts:
                cursor.execute("""
                INSERT INTO simulation_artifacts (
                    artifact_code, task_code, artifact_type, filename, file_path, content_type
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    artifact["artifact_code"],
                    artifact["task_code"],
                    artifact["artifact_type"],
                    artifact["filename"],
                    artifact["file_path"],
                    artifact["content_type"],
                ))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_task(task_code):
    task_code = normalize_task_code(task_code)
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
            SELECT *
            FROM simulation_tasks
            WHERE task_code = %s
            """, (task_code,))
            row = cursor.fetchone()
    finally:
        conn.close()

    return _record_from_row(row)


def get_user_task(task_code, user_id):
    task_code = normalize_task_code(task_code)
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
            SELECT *
            FROM simulation_tasks
            WHERE task_code = %s
                AND user_id = %s
            """, (task_code, user_id))
            row = cursor.fetchone()
    finally:
        conn.close()

    return _record_from_row(row)


def list_user_tasks(user_id):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
            SELECT *
            FROM simulation_tasks
            WHERE user_id = %s
            ORDER BY submitted_at DESC, id DESC
            """, (user_id,))
            rows = cursor.fetchall()
    finally:
        conn.close()

    return [_record_from_row(row, []) for row in rows]


def mark_interrupted_tasks_failed():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
            UPDATE simulation_tasks
            SET status = 'failed',
                message = 'Service restarted before the task finished',
                error_message = 'Service restarted before the task finished',
                finished_at = NOW()
            WHERE status IN ('queued', 'running', 'reporting')
            """)
        conn.commit()
    except Exception:
        conn.rollback()
    finally:
        conn.close()
