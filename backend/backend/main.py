import asyncio

import uvicorn
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from starlette.responses import JSONResponse

from backend import config
from backend.auth.adapters.apikey_router import apikey_router
from backend.auth.adapters.auth_user_router import include_fastapi_users_routers
from backend.auth.application.apikey_service import InvalidApikeyFormat
from backend.auth.domain.exceptions import AuthenticationError
from backend.shared.exceptions import ItemNotExist, ItemAlreadyExist, ValidationError
from backend.startup_service import StartupShutdownManager
from backend.subscription.adapters.plan_api import plan_router
from backend.subscription.adapters.subscription_api import subscription_router
from backend.subscription.domain.exceptions import ActiveStatusConflict
from backend.webhook.adapters.webhook_api import webhook_router

logger.remove()

logger.add(
    sink=lambda msg: print(msg, end=""),  # Вывод в stdout без лишних переносов строк
    format="<level>{message}</level>",  # Оставляем только уровень лога и сообщение
    colorize=True  # Оставляем цвет
)

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


@app.exception_handler(AuthenticationError)
async def handle_authentication_error(_request: Request, _exc: AuthenticationError):
    raise HTTPException(status_code=400, detail="BAD_CREDENTIALS")


@app.exception_handler(InvalidApikeyFormat)
async def handle_invalid_apikey_format_error(_request: Request, _exc: InvalidApikeyFormat):
    raise HTTPException(status_code=400, detail="Invalid apikey format")


async def main():
    conf = uvicorn.Config(app, host=config.HOST, port=config.PORT)
    server = uvicorn.Server(conf)
    await server.serve()


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    startup_shutdown = StartupShutdownManager(db_recreate=False)

    try:
        loop.run_until_complete(startup_shutdown.on_startup())
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        loop.run_until_complete(startup_shutdown.on_shutdown())
    finally:
        loop.close()
