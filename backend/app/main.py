from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

from app.core.database import init_db
from app.core.config import settings
from app.api.routers import questions, results, grading, upload, reports

# Load environment variables
load_dotenv()

app = FastAPI(title=settings.PROJECT_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
def startup_event():
    init_db()

@app.get("/")
async def root():
    return {"message": "Otomatik Sınav Değerlendirme Sistemi - Aktif"}

@app.get("/model-info")
async def model_info():
    """Get information about the OCR backend."""
    return {
        "model_type": "Google Gemini Flash",
        "provider": "Google Cloud",
        "status": "Active"
    }

# Include Routers
app.include_router(questions.router, prefix="/api", tags=["Sınav Soruları"])
app.include_router(results.router, prefix="/api", tags=["Öğrenci Sonuçları"])
app.include_router(grading.router, prefix="/api", tags=["Puanlama"])
app.include_router(reports.router, prefix="/api", tags=["Raporlama"])
app.include_router(upload.router, tags=["Upload"])
