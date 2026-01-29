from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.domain import OgrenciSonuclari
from app.schemas.dtos import OgrenciSonucuResponse

router = APIRouter()

@router.get("/ogrenci-sonuclari", response_model=List[OgrenciSonucuResponse])
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
