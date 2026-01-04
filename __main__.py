from fastapi import (
    FastAPI,
    Request,
)
from fastapi.middleware.cors import (
    CORSMiddleware,
)
import logging
import os
from prometheus_fastapi_instrumentator import (
    Instrumentator,
)
import shutil
import time
import uvicorn

from app.auth.router import router as auth_router
from app.chats.router import router as chats_router
from app.config import settings
from app.contacts.router import router as contacts_router
from app.rooms.router import router as rooms_router
from app.users.router import router as users_router
from app.utils.engine import init_engine_app
from app.web_sockets.router import router as web_sockets_router


def setup_prometheus(app: FastAPI) -> None:
    try:
        instrumentator = Instrumentator(
            should_group_status_codes=False,
            should_ignore_untemplated=True,
            should_instrument_requests_inprogress=True,
            inprogress_name="inprogress",
            inprogress_labels=True,
        )
        instrumentator.instrument(app).expose(
            app,
            should_gzip=True,
            name="prometheus_metrics",
            include_in_schema=False,
        )
    except Exception as e:
        logger.warning(f"Prometheus metrics setup skipped: {e}")


def set_multiproc_dir() -> None:
    shutil.rmtree(settings.PROMETHEUS_DIR, ignore_errors=True)
    os.makedirs(settings.PROMETHEUS_DIR, exist_ok=True)
    os.environ["prometheus_multiproc_dir"] = str(
        settings.PROMETHEUS_DIR.expanduser().absolute(),
    )
    os.environ["PROMETHEUS_MULTIPROC_DIR"] = str(
        settings.PROMETHEUS_DIR.expanduser().absolute(),
    )


logger = logging.getLogger(__name__)

if settings.DEBUG == "info":
    chat_app = FastAPI(
        docs_url="/docs",
        redoc_url="/redocs",
        title="Brave Chat Server",
        description="The server side of Brave Chat.",
        version="1.0",
        openapi_url="/api/v1/openapi.json",
    )
else:
    chat_app = FastAPI(
        docs_url=None,
        redoc_url=None,
        title=None,
        description=None,
        version=None,
        openapi_url=None,
    )

origins = [
    "http://127.0.0.1:8000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5500",
    "http://localhost:8000",
    "http://localhost:3000",
    "http://localhost:5500",
    "null",  
]

origins.extend(settings.cors_origins)

chat_app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@chat_app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


setup_prometheus(chat_app)


@chat_app.on_event("startup")
async def startup():
    await init_engine_app(chat_app)


@chat_app.on_event("shutdown")
async def shutdown():
    await chat_app.state.db_engine.dispose()


@chat_app.get("/api")
async def root():
    return {"message": "Welcome to the Brave Chat Server."}


chat_app.include_router(auth_router, tags=["Auth"])
chat_app.include_router(users_router, tags=["User"])
chat_app.include_router(contacts_router, tags=["Contact"])
chat_app.include_router(chats_router, tags=["Chat"])
chat_app.include_router(rooms_router, tags=["Room"])
chat_app.include_router(web_sockets_router, tags=["Socket"])


def serve() -> None:
    try:
        set_multiproc_dir()
        uvicorn.run(
            chat_app,
            host="0.0.0.0",
            port=8000,
            reload=False,
            log_level="debug",
        )
    except Exception as e:
        print(e)


if __name__ == "__main__":
    serve()
