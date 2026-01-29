from fastapi import APIRouter, UploadFile, File, HTTPException
from pdf2image import convert_from_bytes
from PIL import Image
import io
import os
import uuid
import json

from app.core.config import settings
from app.services.ocr import process_image_ocr, anonymize_student_data_local

router = APIRouter()

# Use settings for Poppler Path
POPPLER_PATH = settings.POPPLER_PATH

@router.post("/upload-generic")
async def upload_generic_pdf(file: UploadFile = File(...)):
    """
    Endpoint for uploading Answer Key or Rubric files.
    Performs OCR with a 'Full Text' focused prompt to get the global context.
    Returns the combined text from all pages.
    """
    try:
        contents = await file.read()
        
        # Determine if file is PDF or image
        images = []
        if file.filename.lower().endswith('.pdf'):
            if POPPLER_PATH and os.path.exists(POPPLER_PATH):
                images = convert_from_bytes(contents, poppler_path=POPPLER_PATH, dpi=300)
            else:
                images = convert_from_bytes(contents, dpi=300)
        else:
            try:
                image = Image.open(io.BytesIO(contents))
                images = [image]
            except Exception as e:
                raise HTTPException(status_code=400, detail="Desteklenmeyen dosya formatı.")
        
        extracted_text_parts = []
        
        # Prompt explicitly for full text extraction without JSON formatting
        generic_prompt = "Bu belgedeki tüm metni olduğu gibi, satır satır dışarı aktar. Başlıkları ve yapıyı korumaya çalış. JSON formatı kullanma, sadece saf metin ver."

        for i, image in enumerate(images):
            try:
                ocr_result = process_image_ocr(image, prompt=generic_prompt)
                
                # We expect 'raw_text' or 'normalized_text'
                text_content = ocr_result.get('raw_text') or ocr_result.get('normalized_text', '')
                extracted_text_parts.append(text_content)
                
            except Exception as ocr_error:
                print(f"Page {i+1} error: {ocr_error}")
                extracted_text_parts.append("")
        
        full_text = "\n\n".join(extracted_text_parts)
        
        return {
            "success": True,
            "filename": file.filename,
            "text": full_text
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dosya işlenirken hata: {str(e)}")


@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Endpoint to upload a PDF or image file, perform OCR using Gemini Vision,
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
            if POPPLER_PATH and os.path.exists(POPPLER_PATH):
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
        
        all_student_data = {}
        
        for i, image in enumerate(images):
            # Apply local anonymization (Redact Name/Number)
            # This happens BEFORE saving and BEFORE Gemini OCR
            image, page_student_data = anonymize_student_data_local(image)
            images[i] = image # Update list with redacted image
            
            # Merge found data
            if page_student_data:
                all_student_data.update(page_student_data)
             
            # Additional save to explicit 'anonymized_uploads' folder as requested
            try:
                # Use settings or relative path (assuming cwd is backend root)
                anon_dir = os.path.join(settings.BASE_DIR, "anonymized_uploads")
                os.makedirs(anon_dir, exist_ok=True)
                anon_filename = f"anon_{request_id}_page_{i+1}.png"
                image.save(os.path.join(anon_dir, anon_filename), "PNG")
            except Exception as save_err:
                print(f"Warning: Could not save backup anonymized image: {save_err}")
            
        # Save extracted student data
        if all_student_data:
            try:
                results_dir = os.path.join(settings.BASE_DIR, "results")
                os.makedirs(results_dir, exist_ok=True)
                student_data_path = os.path.join(results_dir, f"{request_id}_student.json")
                with open(student_data_path, "w", encoding="utf-8") as f:
                    json.dump(all_student_data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"Warning: Could not save student data: {e}")
            
        extracted_data = []
        
        for i, image in enumerate(images):
            try:
                # Perform OCR and normalization using our utility module
                ocr_result = process_image_ocr(image, debug_dir=None)
                
                extracted_data.append({
                    "page": i + 1,
                    "text": ocr_result['normalized_text'],
                    "raw_text": ocr_result['raw_text'],
                    "normalized_text": ocr_result['normalized_text'],
                    "structured_data": ocr_result.get('structured_data', []),  # Pass structured questions
                    "processing_steps": ocr_result.get('processing_steps', [])
                })
                
            except Exception as ocr_error:
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
        results_dir = os.path.join(settings.BASE_DIR, "results")
        os.makedirs(results_dir, exist_ok=True)
        with open(os.path.join(results_dir, f"{response_data['id']}.json"), "w", encoding="utf-8") as f:
            json.dump(response_data, f, ensure_ascii=False, indent=2)
            
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Dosya işlenirken bir hata oluştu: {str(e)}"
        )
