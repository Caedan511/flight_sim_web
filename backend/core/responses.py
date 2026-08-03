from fastapi import HTTPException
from fastapi.responses import JSONResponse


def api_response(success, message, data=None):
    return {
        "success": success,
        "message": message,
        "data": data,
    }


def http_exception_handler(request, exc):
    message = exc.detail
    if isinstance(message, dict):
        message = message.get("message", "Request failed")

    return JSONResponse(
        status_code=exc.status_code,
        content=api_response(False, message),
        headers=getattr(exc, "headers", None),
    )


def register_exception_handlers(app):
    app.add_exception_handler(HTTPException, http_exception_handler)
