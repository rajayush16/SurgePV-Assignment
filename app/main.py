from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.errors import error_response
from app.routes.issues import router as issues_router
from app.routes.reports import router as reports_router


app = FastAPI(title="Issue Tracker API")
app.include_router(issues_router)
app.include_router(reports_router)


@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=error_response("VALIDATION_ERROR", "Request validation failed", {"errors": exc.errors()}),
    )


@app.exception_handler(StarletteHTTPException)
def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        content = exc.detail
    else:
        content = error_response("HTTP_ERROR", str(exc.detail))
    return JSONResponse(status_code=exc.status_code, content=content)
