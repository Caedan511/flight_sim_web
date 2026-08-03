import base64
import binascii
import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone

from backend.core.config import Config


class TokenError(Exception):
    pass


def _base64url_encode(data):
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _base64url_decode(data):
    padding = "=" * (-len(data) % 4)
    try:
        return base64.urlsafe_b64decode((data + padding).encode("ascii"))
    except (binascii.Error, ValueError) as exc:
        raise TokenError("Invalid token") from exc


def _json_dumps(data):
    return json.dumps(data, separators=(",", ":"), sort_keys=True).encode("utf-8")


def _ensure_supported_algorithm():
    if Config.JWT_ALGORITHM != "HS256":
        raise TokenError("Unsupported JWT algorithm")


def create_access_token(user):
    _ensure_supported_algorithm()

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=Config.JWT_EXPIRE_MINUTES)
    header = {
        "alg": Config.JWT_ALGORITHM,
        "typ": "JWT",
    }
    payload = {
        "sub": str(user["id"]),
        "uid": user["uid"],
        "username": user["username"],
        "role": user["role"],
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }

    signing_input = (
        f"{_base64url_encode(_json_dumps(header))}."
        f"{_base64url_encode(_json_dumps(payload))}"
    )
    signature = hmac.new(
        Config.JWT_SECRET_KEY.encode("utf-8"),
        signing_input.encode("ascii"),
        hashlib.sha256,
    ).digest()

    return f"{signing_input}.{_base64url_encode(signature)}"


def decode_access_token(token):
    _ensure_supported_algorithm()

    try:
        header_part, payload_part, signature_part = token.split(".")
    except ValueError as exc:
        raise TokenError("Invalid token") from exc

    signing_input = f"{header_part}.{payload_part}"
    expected_signature = hmac.new(
        Config.JWT_SECRET_KEY.encode("utf-8"),
        signing_input.encode("ascii"),
        hashlib.sha256,
    ).digest()
    actual_signature = _base64url_decode(signature_part)

    if not hmac.compare_digest(expected_signature, actual_signature):
        raise TokenError("Invalid token")

    try:
        header = json.loads(_base64url_decode(header_part))
        payload = json.loads(_base64url_decode(payload_part))
    except (json.JSONDecodeError, ValueError) as exc:
        raise TokenError("Invalid token") from exc

    if header.get("alg") != Config.JWT_ALGORITHM or header.get("typ") != "JWT":
        raise TokenError("Invalid token")

    expires_at = payload.get("exp")
    if not isinstance(expires_at, int):
        raise TokenError("Invalid token")

    if expires_at <= int(datetime.now(timezone.utc).timestamp()):
        raise TokenError("Token has expired")

    return payload
