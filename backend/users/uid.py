import uuid


USER_UID_PREFIX = "U"
USER_UID_WIDTH = 6


def format_user_uid(user_id):
    return f"{USER_UID_PREFIX}{int(user_id):0{USER_UID_WIDTH}d}"


def make_pending_user_uid():
    return f"T{uuid.uuid4().hex[:12].upper()}"


def normalize_user_uid(uid):
    return uid.strip().upper()
