from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Body
from fastapi.middleware.cors import CORSMiddleware
from pdf2image import convert_from_bytes
from PIL import Image
from sqlalchemy.orm import Session
import io
import os
import uuid
import json
from typing import List, Dict, Any
from dotenv import load_dotenv
from ocr_utils import process_image_ocr, anonymize_student_data_local
from database import get_db, init_db
from models import SinavSorulari, OgrenciSonuclari
from schemas import (
    SinavSorusuCreate, SinavSorusuUpdate, SinavSorusuResponse,
    OgrenciSonucuCreate, OgrenciSonucuResponse
)

# Load environment variables
load_dotenv()

app = FastAPI(title="Otomatik Sınav Değerlendirme Sistemi")

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

# Poppler yolu (Windows için PDF işleme)
# Poppler yolu (Windows için PDF işleme)
# Öncelik 1: Proje içi lokal kurulum
base_dir = os.path.dirname(os.path.abspath(__file__))
local_poppler = os.path.join(base_dir, 'bin', 'poppler-24.02.0', 'Library', 'bin')

if os.path.exists(local_poppler):
    POPPLER_PATH = local_poppler
else:
    # Öncelik 2: Sistem geneli kurulumlar
    POPPLER_PATH = r'C:\Program Files\poppler\Library\bin'  
    if not os.path.exists(POPPLER_PATH):
        POPPLER_PATH = r'C:\Program Files\poppler\bin'

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


# ==================== SINAV SORULARI CRUD ====================

@app.post("/api/sinav-sorulari", response_model=SinavSorusuResponse)
def create_sinav_sorusu(soru: SinavSorusuCreate, db: Session = Depends(get_db)):
    """Yeni sınav sorusu ekle."""
    db_soru = SinavSorulari(**soru.model_dump())
    db.add(db_soru)
    db.commit()
    db.refresh(db_soru)
    return db_soru


@app.get("/api/sinav-sorulari", response_model=List[SinavSorusuResponse])
def get_sinav_sorulari(sinav_id: str = None, db: Session = Depends(get_db)):
    """Tüm sınav sorularını getir veya sinav_id'ye göre filtrele."""
    query = db.query(SinavSorulari)
    if sinav_id:
        query = query.filter(SinavSorulari.sinav_id == sinav_id)
    return query.order_by(SinavSorulari.sinav_id, SinavSorulari.soru_no).all()


@app.get("/api/sinav-sorulari/{soru_id}", response_model=SinavSorusuResponse)
def get_sinav_sorusu(soru_id: int, db: Session = Depends(get_db)):
    """Belirli bir soruyu getir."""
    soru = db.query(SinavSorulari).filter(SinavSorulari.id == soru_id).first()
    if not soru:
        raise HTTPException(status_code=404, detail="Soru bulunamadı")
    return soru


@app.put("/api/sinav-sorulari/{soru_id}", response_model=SinavSorusuResponse)
def update_sinav_sorusu(soru_id: int, updates: SinavSorusuUpdate, db: Session = Depends(get_db)):
    """Soruyu güncelle."""
    soru = db.query(SinavSorulari).filter(SinavSorulari.id == soru_id).first()
    if not soru:
        raise HTTPException(status_code=404, detail="Soru bulunamadı")
    
    update_data = updates.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(soru, key, value)
    
    db.commit()
    db.refresh(soru)
    return soru


@app.delete("/api/sinav-sorulari/{soru_id}")
def delete_sinav_sorusu(soru_id: int, db: Session = Depends(get_db)):
    """Soruyu sil."""
    soru = db.query(SinavSorulari).filter(SinavSorulari.id == soru_id).first()
    if not soru:
        raise HTTPException(status_code=404, detail="Soru bulunamadı")
    
    db.delete(soru)
    db.commit()
    return {"message": "Soru silindi"}


# ==================== ÖĞRENCI SONUÇLARI ====================

@app.get("/api/ogrenci-sonuclari", response_model=List[OgrenciSonucuResponse])
def get_ogrenci_sonuclari(
    sinav_id: str = None, 
    ogrenci_id: str = None, 
    db: Session = Depends(get_db)
):
    """Öğrenci sonuçlarını getir."""
    query = db.query(OgrenciSonuclari)
    if sinav_id:
        query = query.filter(OgrenciSonuclari.sinav_id == sinav_id)
    if ogrenci_id:
        query = query.filter(OgrenciSonuclari.ogrenci_id == ogrenci_id)
    return query.all()


# ==================== PUANLAMA ====================

@app.post("/api/puanla-direkt")
def puanla_direkt(
    ideal_cevap: str = Body(..., embed=True),
    ogrenci_cevabi: str = Body(..., embed=True),
    soru_metni: str = Body("", embed=True),
    answer_key_text: str = Body(None, embed=True),
    rubric_text: str = Body(None, embed=True)
):
    """
    Doğrudan puanlama - veritabanı gerektirmez.
    İdeal cevap ve öğrenci cevabını karşılaştırarak puan verir.
    """
    from scoring import evaluate_answer
    
    if not ideal_cevap and not answer_key_text:
        # We need at least one source of truth
        raise HTTPException(status_code=400, detail="İdeal cevap veya Cevap Anahtarı gerekli.")
    
    # Perform evaluation
    result = evaluate_answer(
        ideal_cevap=ideal_cevap,
        ogrenci_cevabi=ogrenci_cevabi,
        soru_metni=soru_metni,
        anahtar_kelimeler="",
        answer_key_text=answer_key_text,
        rubric_text=rubric_text
    )
    
    return {
        "success": True,
        "bert_skoru": result['bert_skoru'],
        "llm_skoru": result['llm_skoru'],
        "final_puan": result['final_puan'],
        "yorum": result['yorum']
    }


@app.post("/api/puanla")
def puanla_cevap(
    sinav_id: str = Body(..., embed=True),
    soru_no: int = Body(..., embed=True),
    ogrenci_id: str = Body(..., embed=True),
    ogrenci_cevabi: str = Body(..., embed=True),
    answer_key_text: str = Body(None, embed=True),
    rubric_text: str = Body(None, embed=True),
    db: Session = Depends(get_db)
):
    """
    Veritabanından ideal cevabı alarak puanlama yapar.
    Önce Hoca Panelinden soruyu eklemeniz gerekir.
    """
    from scoring import evaluate_answer
    
    # Get the question and ideal answer from database (case-insensitive)
    from sqlalchemy import func
    soru = db.query(SinavSorulari).filter(
        func.lower(SinavSorulari.sinav_id) == sinav_id.lower(),
        SinavSorulari.soru_no == soru_no
    ).first()
    
    if not soru and not answer_key_text:
         # If allowing generic scoring without DB question, remove this check or adapt. 
         # But this endpoint is specifically for DB questions.
        raise HTTPException(status_code=404, detail=f"Soru bulunamadı. sinav_id='{sinav_id}', soru_no={soru_no}")
    
    ideal_cevap = soru.ideal_cevap if soru else ""
    soru_metni_db = soru.soru_metni if soru else ""
    anahtar_kelimeler = soru.anahtar_kelimeler or ""
    
    # Perform evaluation
    result = evaluate_answer(
        ideal_cevap=ideal_cevap,
        ogrenci_cevabi=ogrenci_cevabi,
        soru_metni=soru_metni_db,
        anahtar_kelimeler=anahtar_kelimeler,
        answer_key_text=answer_key_text,
        rubric_text=rubric_text
    )
    
    # Save result to database
    sonuc = OgrenciSonuclari(
        sinav_id=sinav_id,
        ogrenci_id=ogrenci_id,
        soru_no=soru_no,
        ogrenci_cevabi=ogrenci_cevabi,
        bert_skoru=result['bert_skoru'],
        llm_skoru=result['llm_skoru'],
        final_puan=result['final_puan'],
        yorum=result['yorum']
    )
    db.add(sonuc)
    db.commit()
    db.refresh(sonuc)
    
    return {
        "success": True,
        "sonuc_id": sonuc.id,
        "bert_skoru": result['bert_skoru'],
        "llm_skoru": result['llm_skoru'],
        "final_puan": result['final_puan'],
        "yorum": result['yorum']
    }


# ==================== OCR UPLOAD ====================


# ==================== OCR UPLOAD ====================

@app.post("/upload-generic")
async def upload_generic_pdf(file: UploadFile = File(...)):
    """
    Endpoint for uploading Answer Key or Rubric files.
    Performs OCR with a 'Full Text' focused prompt to get the global context.
    Returns the combined text from all pages.
    """
    try:
        contents = await file.read()
        request_id = str(uuid.uuid4())
        
        # Determine if file is PDF or image
        images = []
        if file.filename.lower().endswith('.pdf'):
            if os.path.exists(POPPLER_PATH):
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


@app.post("/upload")
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
        
        for i, image in enumerate(images):
            # Apply local anonymization (Redact Name/Number)
            # This happens BEFORE saving and BEFORE Gemini OCR
            image = anonymize_student_data_local(image)
            images[i] = image # Update list with redacted image
             
            # Additional save to explicit 'anonymized_uploads' folder as requested
            try:
                anon_dir = os.path.join(base_dir, "anonymized_uploads")
                os.makedirs(anon_dir, exist_ok=True)
                anon_filename = f"anon_{request_id}_page_{i+1}.png"
                image.save(os.path.join(anon_dir, anon_filename), "PNG")
            except Exception as save_err:
                print(f"Warning: Could not save backup anonymized image: {save_err}")
            
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

