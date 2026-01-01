from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pdf2image import convert_from_bytes
from PIL import Image
import io
import os
import uuid
import json
from typing import List, Dict, Any
from dotenv import load_dotenv
from ocr_utils import process_image_ocr

# Load environment variables
load_dotenv()

app = FastAPI(title="Exam Grading System Backend - TrOCR Handwriting Recognition")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Poppler yolu (Windows için PDF işleme)
POPPLER_PATH = r'C:\Program Files\poppler\Library\bin'  
if not os.path.exists(POPPLER_PATH):
    POPPLER_PATH = r'C:\Program Files\poppler\bin'

@app.get("/")
async def root():
    return {"message": "Exam Grading System Backend - TrOCR Handwriting Recognition Active"}

@app.get("/model-info")
async def model_info():
    """Get information about the OCR backend."""
    return {
        "model_type": "Google Gemini 1.5 Flash",
        "provider": "Google Cloud",
        "status": "Active"
    }


@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Endpoint to upload a PDF or image file, perform OCR using EasyOCR (Turkish),
    normalize text, and return extracted text.
    """
    try:
        contents = await file.read()
        
        # Generate a unique ID for this request
        request_id = str(uuid.uuid4())
        
        # Determine if file is PDF or image
        images = []
        if file.filename.lower().endswith('.pdf'):
            # Convert PDF to images with higher DPI for better OCR
            # DPI=300 is standard for high quality OCR
            if os.path.exists(POPPLER_PATH):
                images = convert_from_bytes(contents, poppler_path=POPPLER_PATH, dpi=300)
            else:
                images = convert_from_bytes(contents, dpi=300)
        else:
            # Direct image file
            try:
                image = Image.open(io.BytesIO(contents))
                images = [image]
            except Exception as e:
                raise HTTPException(
                    status_code=400, 
                    detail="Desteklenmeyen dosya formatı. Lütfen PDF veya görsel dosyası yükleyin."
                )
        
        # Save processed images for inspection
        save_dir = os.path.join("processed_images", request_id)
        os.makedirs(save_dir, exist_ok=True)
        
        for i, image in enumerate(images):
            image_path = os.path.join(save_dir, f"page_{i+1}.png")
            image.save(image_path, "PNG")
            
        extracted_data = []
        
        for i, image in enumerate(images):
            try:
                # Perform OCR and normalization using our utility module
                # Create a specific debug dir for this page's lines
                page_debug_dir = os.path.join(save_dir, f"page_{i+1}")
                os.makedirs(page_debug_dir, exist_ok=True)
                
                ocr_result = process_image_ocr(image, debug_dir=page_debug_dir)
                
                extracted_data.append({
                    "page": i + 1,
                    "text": ocr_result['normalized_text'],  # Normalized text for display
                    "raw_text": ocr_result['raw_text'],     # Raw OCR output
                    "normalized_text": ocr_result['normalized_text'],  # Explicitly include normalized
                    "processing_steps": ocr_result.get('processing_steps', [])  # Processing steps for visualization
                })
                
            except Exception as ocr_error:
                # Handle OCR errors gracefully for individual pages
                extracted_data.append({
                    "page": i + 1,
                    "text": "",
                    "raw_text": "",
                    "normalized_text": "",
                    "error": str(ocr_error)
                })
        
        response_data = {
            "id": request_id,
            "filename": file.filename,
            "page_count": len(images),
            "pages": extracted_data
        }
        
        # Save results to file
        os.makedirs("results", exist_ok=True)
        with open(f"results/{response_data['id']}.json", "w", encoding="utf-8") as f:
            json.dump(response_data, f, ensure_ascii=False, indent=2)
            
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Dosya işlenirken bir hata oluştu: {str(e)}"
        )

