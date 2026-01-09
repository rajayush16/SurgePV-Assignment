from typing import Any

from fastapi import HTTPException, status


def error_response(code: str, message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"error": {"code": code, "message": message}}
    if details is not None:
        payload["error"]["details"] = details
    return payload


def http_error(code: str, message: str, status_code: int, details: dict[str, Any] | None = None) -> HTTPException:
    return HTTPException(status_code=status_code, detail=error_response(code, message, details))


def not_found(entity: str, details: dict[str, Any] | None = None) -> HTTPException:
    return http_error("NOT_FOUND", f"{entity} not found", status.HTTP_404_NOT_FOUND, details)


def conflict(code: str, message: str, details: dict[str, Any] | None = None) -> HTTPException:
    return http_error(code, message, status.HTTP_409_CONFLICT, details)


def bad_request(code: str, message: str, details: dict[str, Any] | None = None) -> HTTPException:
    return http_error(code, message, status.HTTP_400_BAD_REQUEST, details)
