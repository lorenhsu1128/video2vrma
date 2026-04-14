import asyncio
import logging
from contextlib import asynccontextmanager
from logging.handlers import RotatingFileHandler

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import LOG_DIR, TMP
from app.core.gpu_worker import GPUWorker
from app.core.task_manager import TaskManager
from app.routers import history as history_router
from app.routers import system as system_router
from app.routers import tasks as tasks_router
from app.routers import upload as upload_router

log = logging.getLogger("video2vrma")


def _configure_logging() -> None:
    """Phase 6d：集中設定 app.* 與 video2vrma logger，避免被 uvicorn 吞。

    呼叫多次冪等：若 root logger 已經有同名檔案 handler，直接 return。
    """
    root = logging.getLogger()
    root.setLevel(logging.INFO)

    fmt = logging.Formatter(
        "%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    has_file_handler = any(
        isinstance(h, RotatingFileHandler)
        and getattr(h, "_video2vrma", False)
        for h in root.handlers
    )
    if not has_file_handler:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        fh = RotatingFileHandler(
            LOG_DIR / "backend.log",
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8",
        )
        fh.setFormatter(fmt)
        fh.setLevel(logging.INFO)
        fh._video2vrma = True  # type: ignore[attr-defined]
        root.addHandler(fh)

    has_stream_handler = any(
        isinstance(h, logging.StreamHandler) and not isinstance(h, RotatingFileHandler)
        for h in root.handlers
    )
    if not has_stream_handler:
        sh = logging.StreamHandler()
        sh.setFormatter(fmt)
        sh.setLevel(logging.INFO)
        root.addHandler(sh)


def create_app(pipeline_module=None) -> FastAPI:
    _configure_logging()

    if pipeline_module is None:
        from app.services import pipeline as pipeline_module  # noqa: PLW0127

    upload_dir = TMP / "uploads"
    work_dir = TMP / "tasks"
    history_dir = TMP / "history"
    upload_dir.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)
    history_dir.mkdir(parents=True, exist_ok=True)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.task_manager = TaskManager(history_dir=history_dir)
        app.state.task_manager.load_history()
        app.state.upload_dir = upload_dir
        app.state.gpu_worker = GPUWorker(
            task_manager=app.state.task_manager,
            pipeline_module=pipeline_module,
            work_dir=work_dir,
        )
        await app.state.gpu_worker.start()

        async def periodic_cleanup():
            while True:
                await asyncio.sleep(3600)
                expired = app.state.task_manager.cleanup_old_tasks()
                if expired:
                    log.info("cleaned up %d old tasks", len(expired))

        cleanup_task = asyncio.create_task(periodic_cleanup())
        try:
            yield
        finally:
            cleanup_task.cancel()
            await app.state.gpu_worker.stop()

    app = FastAPI(title="video2vrma", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(upload_router.router, prefix="/api")
    app.include_router(tasks_router.router, prefix="/api")
    app.include_router(history_router.router, prefix="/api")
    app.include_router(system_router.router, prefix="/api")
    return app


def __getattr__(name):
    # 延遲到真的有人 (uvicorn) 取 app 才實例化，避免 import app.main 就觸發
    # services.pipeline → vendor_paths 的重型 side effect。
    if name == "app":
        return create_app()
    raise AttributeError(name)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
