from app.routers import models, news, social, trades
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Live Trade Bench API",
    description="FastAPI backend for trading dashboard with models, trades, and news data",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(models.router)
app.include_router(trades.router)
app.include_router(news.router)
app.include_router(social.router)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Live Trade Bench API",
        "version": "1.0.0",
        "endpoints": {
            "models": "/api/models",
            "trades": "/api/trades",
            "news": "/api/news",
            "social": "/api/social",
            "docs": "/docs",
            "redoc": "/redoc",
        },
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "API is running"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
