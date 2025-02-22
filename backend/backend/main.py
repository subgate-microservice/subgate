import asyncio

import uvicorn
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from starlette.responses import JSONResponse

from backend import config
from backend.auth.adapters.apikey_router import apikey_router
from backend.auth.adapters.fastapi_user_routers import include_fastapi_users_routers
from backend.auth.infra.apikey.apikey__auth_closure_factory import NotAuthenticated
from backend.shared.exceptions import ItemNotExist, ItemAlreadyExist, ValidationError
from backend.startup_service import run_preparations, run_workers
from backend.subscription.adapters.plan_api import plan_router
from backend.subscription.adapters.subscription_api import subscription_router
from backend.subscription.domain.exceptions import ActiveStatusConflict
from backend.webhook.adapters.webhook_api import webhook_router

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost"],  # Allowed origins
    allow_credentials=True,
    allow_methods=["*"],  # Allowed HTTP methods
    allow_headers=["*"],  # Allowed headers
)

app.include_router(subscription_router, prefix="/api/v1")
app.include_router(plan_router, prefix="/api/v1")
app.include_router(webhook_router, prefix="/api/v1")
app.include_router(apikey_router, prefix="/api/v1")
include_fastapi_users_routers(app)


@app.exception_handler(PermissionError)
async def handle_permission_error(_request: Request, _exc: PermissionError):
    logger.error("PermissionError")
    return JSONResponse(
        status_code=403,
        content={},
    )


@app.exception_handler(NotAuthenticated)
async def handle_not_authenticated(_request: Request, exc: NotAuthenticated):
    logger.error(exc)
    return JSONResponse(
        status_code=401,
        content={},
    )


@app.exception_handler(ItemNotExist)
async def handle_item_not_exist(_request: Request, exc: ItemNotExist):
    logger.error(exc)
    return JSONResponse(
        status_code=404,
        content=exc.to_json(),
    )


@app.exception_handler(ItemAlreadyExist)
async def handle_item_already_exist(_request: Request, exc: ItemAlreadyExist):
    logger.error(exc)
    return JSONResponse(
        status_code=409,
        content=exc.to_json(),
    )


@app.exception_handler(ActiveStatusConflict)
async def handle_item_active_status_conflict(_request: Request, exc: ActiveStatusConflict):
    logger.error(exc)
    return JSONResponse(
        status_code=409,
        content=exc.to_json(),
    )


# @app.exception_handler(RequestValidationError)
async def handle_request_validation_error(_request: Request, exc: RequestValidationError):
    logger.error(exc)
    detail = [
        ValidationError(
            field=x["loc"][1],
            value=x["input"],
            value_type=x["input"].__class__.__name__,
            message=x["msg"],
        ).to_json()
        for x in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={
            "exception_code": "request_validation_error",
            "message": str(exc),
            "detail": detail,
        },
    )


@app.exception_handler(ValidationError)
async def handle_request_validation_error(_request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=422,
        content=[exc.to_json()]
    )


async def main():
    await run_preparations()
    run_workers()
    conf = uvicorn.Config(app, host=config.HOST, port=config.PORT)
    server = uvicorn.Server(conf)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
