import json

from fastapi import Request, Response
from fastapi.responses import JSONResponse

from app.shared.datetimes import now_iso

MESSAGE_BY_METHOD = {
    "GET": "Operación exitosa",
    "POST": "Recurso creado",
    "PATCH": "Recurso actualizado",
    "DELETE": "Recurso eliminado",
}


def success_response(code: int, message: str, data: object) -> dict:
    return {
        "code": code,
        "success": True,
        "message": message,
        "timestamp": now_iso(),
        "data": data,
    }


def error_response(
    code: int,
    message: str,
    *,
    error: str | None = None,
    errors: dict[str, dict[str, str]] | None = None,
) -> dict:
    body: dict = {
        "code": code,
        "success": False,
        "message": message,
        "timestamp": now_iso(),
        "data": None,
    }

    if errors is not None:
        body["errors"] = errors
    elif error is not None:
        body["error"] = error

    return body


async def envelope_middleware(request: Request, call_next) -> Response:
    response: Response = await call_next(request)

    if not request.url.path.startswith("/api") or not 200 <= response.status_code < 400:
        return response

    body_bytes = getattr(response, "body", None)
    if body_bytes is None:
        body_bytes = b"".join([chunk async for chunk in response.body_iterator])

    data = json.loads(body_bytes)
    message = MESSAGE_BY_METHOD.get(request.method, "OK")
    body = success_response(response.status_code, message, data)

    return JSONResponse(status_code=response.status_code, content=body)
