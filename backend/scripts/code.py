import uuid


SCRIPT_CODE_PREFIX = "F"
SCRIPT_CODE_WIDTH = 6


def format_script_code(script_id):
    return f"{SCRIPT_CODE_PREFIX}{int(script_id):0{SCRIPT_CODE_WIDTH}d}"


def make_pending_script_code():
    return f"T{uuid.uuid4().hex[:12].upper()}"


def normalize_script_code(script_code):
    return script_code.strip().upper()
