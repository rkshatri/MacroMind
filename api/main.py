import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import plan, pantry, prefs

# Initialize FastAPI app
app = FastAPI(
    title="MacroMind API",
    description="AI-powered meal planning system",
    version="1.0.0"
)

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with /api prefix
app.include_router(plan.router, prefix="/api", tags=["plan"])
app.include_router(pantry.router, prefix="/api", tags=["pantry"])
app.include_router(prefs.router, prefix="/api", tags=["prefs"])


@app.get("/")
async def root():
    """Root endpoint returning API info."""
    return {
        "message": "MacroMind API",
        "docs": "/docs",
        "openapi": "/openapi.json"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
