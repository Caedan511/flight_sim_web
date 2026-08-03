import uuid


def format_task_code(task_id):
    return f"T{task_id:06d}"


def make_pending_task_code():
    return f"TPENDING{uuid.uuid4().hex[:12].upper()}"


def normalize_task_code(task_code):
    return task_code.strip().upper()
