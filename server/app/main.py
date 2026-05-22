import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import get_settings
from app.database import init_db, AsyncSessionLocal
from app.services.auth_service import ensure_admin_exists

settings = get_settings()


async def run_heartbeat_checker():
    """Background task: periodically check client heartbeats and mark offline."""
    from app.websocket.manager import manager
    while True:
        try:
            await manager.check_heartbeats()
        except Exception:
            pass
        await asyncio.sleep(15)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    async with AsyncSessionLocal() as db:
        await ensure_admin_exists(db)
    heartbeat_task = asyncio.create_task(run_heartbeat_checker())
    yield
    heartbeat_task.cancel()
    try:
        await heartbeat_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title=settings.APP_NAME,
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"service": settings.APP_NAME, "version": "2.0.0", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "ok"}


# Register REST API routers
from app.api import auth, groups, tags, clients, policies, storages, versions, backups, system

app.include_router(auth.router, prefix="/api/v1")
app.include_router(groups.router, prefix="/api/v1")
app.include_router(tags.router, prefix="/api/v1")
app.include_router(clients.router, prefix="/api/v1")
app.include_router(policies.router, prefix="/api/v1")
app.include_router(storages.router, prefix="/api/v1")
app.include_router(versions.router, prefix="/api/v1")
app.include_router(backups.router, prefix="/api/v1")
app.include_router(system.router, prefix="/api/v1")
app.include_router(auth.users_router, prefix="/api/v1")

# Register WebSocket endpoints
from app.websocket.router import websocket_endpoint

app.add_api_websocket_route("/api/v1/ws", websocket_endpoint)
