from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.models.domain import SinavSorulari, OgrenciSonuclari
from app.services.scoring import evaluate_answer

router = APIRouter()

@router.post("/puanla-direkt")
def puanla_direkt(
    soru_no: int = Body(1, embed=True),
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
    
    if not ideal_cevap and not answer_key_text:
        # We need at least one source of truth
        raise HTTPException(status_code=400, detail="İdeal cevap veya Cevap Anahtarı gerekli.")
    
    # Perform evaluation
    result = evaluate_answer(
        soru_no=soru_no,
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
        "max_puan": result.get('max_puan', 100),
        "yorum": result['yorum']
    }


@router.post("/puanla")
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
    
    # Get the question and ideal answer from database (case-insensitive)
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
        rubric_text=rubric_text,
        soru_no=soru_no
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
    "max_puan": result.get('max_puan', 100),
    "yorum": result['yorum']
    }
