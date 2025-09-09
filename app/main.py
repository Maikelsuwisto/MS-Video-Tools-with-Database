import os
import traceback
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

# Import routes
from .routes import health, transcribe

# -----------------------
# FastAPI app
# -----------------------
app = FastAPI(title="MS-Video2Script + Video2SRT Backend")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_coop_coep_headers(request, call_next):
    response = await call_next(request)
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
    return response

# -----------------------
# Serve React build
# -----------------------
build_path = "build"
if not os.path.exists(build_path):
    raise RuntimeError(f"React build folder not found at '{build_path}'")

app.mount("/assets", StaticFiles(directory=os.path.join(build_path, "assets")), name="assets")

# Register routers
app.include_router(health.router)
app.include_router(transcribe.router)

# SPA fallback
@app.get("/{full_path:path}")
async def spa_fallback(full_path: str):
    return FileResponse(os.path.join(build_path, "index.html"))

# Debug exception handler
@app.exception_handler(Exception)
async def debug_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error_type": type(exc).__name__,
            "error_message": str(exc),
            "traceback": traceback.format_exc()
        },
    )
