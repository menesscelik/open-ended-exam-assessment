from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.domain import SinavSorulari
from app.schemas.dtos import SinavSorusuCreate, SinavSorusuUpdate, SinavSorusuResponse

router = APIRouter()

@router.post("/sinav-sorulari", response_model=SinavSorusuResponse)
def create_sinav_sorusu(soru: SinavSorusuCreate, db: Session = Depends(get_db)):
    """Yeni sınav sorusu ekle."""
    db_soru = SinavSorulari(**soru.model_dump())
    db.add(db_soru)
    db.commit()
    db.refresh(db_soru)
    return db_soru


@router.get("/sinav-sorulari", response_model=List[SinavSorusuResponse])
def get_sinav_sorulari(sinav_id: str = None, db: Session = Depends(get_db)):
    """Tüm sınav sorularını getir veya sinav_id'ye göre filtrele."""
    query = db.query(SinavSorulari)
    if sinav_id:
        query = query.filter(SinavSorulari.sinav_id == sinav_id)
    return query.order_by(SinavSorulari.sinav_id, SinavSorulari.soru_no).all()


@router.get("/sinav-sorulari/{soru_id}", response_model=SinavSorusuResponse)
def get_sinav_sorusu(soru_id: int, db: Session = Depends(get_db)):
    """Belirli bir soruyu getir."""
    soru = db.query(SinavSorulari).filter(SinavSorulari.id == soru_id).first()
    if not soru:
        raise HTTPException(status_code=404, detail="Soru bulunamadı")
    return soru


@router.put("/sinav-sorulari/{soru_id}", response_model=SinavSorusuResponse)
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


@router.delete("/sinav-sorulari/{soru_id}")
def delete_sinav_sorusu(soru_id: int, db: Session = Depends(get_db)):
    """Soruyu sil."""
    soru = db.query(SinavSorulari).filter(SinavSorulari.id == soru_id).first()
    if not soru:
        raise HTTPException(status_code=404, detail="Soru bulunamadı")
    
    db.delete(soru)
    db.commit()
    return {"message": "Soru silindi"}
