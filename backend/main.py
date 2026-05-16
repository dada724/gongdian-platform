"""
main.py — FastAPI 入口
工电中心一体化平台后端
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from database import init_db
from routers import auth, modules, subs, users, faults, faults


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行
    init_db()
    print("✅ 工电中心一体化平台后端已启动")
    print("   注册第一个账号将自动获得 developer 权限")
    yield
    # 关闭时执行（如有需要）
    pass


app = FastAPI(title="工电中心一体化平台 API", lifespan=lifespan)

# ── CORS（开发阶段允许所有来源，生产环境请收紧）────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 挂载路由 ────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(modules.router)
app.include_router(subs.router)
app.include_router(users.router)
app.include_router(faults.router)

# ── 静态文件（前端）───────────────────────────────────────────
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "../frontend")
if os.path.isdir(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)