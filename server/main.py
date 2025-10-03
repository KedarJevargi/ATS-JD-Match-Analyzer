import os
from fastapi import FastAPI
import uvicorn

# Import your routers
from routers import pdf_router , jd_router, ats_router  # make sure you have routers/pdf_router.py

PORT = int(os.getenv("PORT", 8000))

app = FastAPI(
    title="My Backend API",
    description="A simple FastAPI service with PDF text extraction",
    version="1.0.0"
)

# Health check endpoint
@app.get("/", tags=["Health Check"])
async def root():
    return {"message": "Server is running 🚀"}

# Register routers
app.include_router(pdf_router.router)   # now /pdfs/... routes will be active
app.include_router(jd_router.router)
app.include_router(ats_router.router)

if __name__ == "__main__":
    # For local dev only; in prod use gunicorn/uvicorn CLI
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=PORT,
        reload=True
    )
