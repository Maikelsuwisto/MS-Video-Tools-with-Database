import os, traceback
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .routes import users, transcribe

app = FastAPI(title="MS-Video Backend")

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

@app.get("/health")
def health(): return {"message": "API is running ✅"}

@app.get("/")
def root(): return {"message": "Backend running ✅"}

# Register routes
app.include_router(users.router)
app.include_router(transcribe.router)

@app.exception_handler(Exception)
def debug_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={
        "error_type": type(exc).__name__,
        "error_message": str(exc),
        "traceback": traceback.format_exc(),
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
