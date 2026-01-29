"""
Pydantic Schemas for API validation
"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# Sınav Soruları Schemas
class SinavSorusuBase(BaseModel):
    sinav_id: str
    soru_no: int
    soru_metni: str
    ideal_cevap: str
    anahtar_kelimeler: Optional[str] = None


class SinavSorusuCreate(SinavSorusuBase):
    pass


class SinavSorusuUpdate(BaseModel):
    soru_metni: Optional[str] = None
    ideal_cevap: Optional[str] = None
    anahtar_kelimeler: Optional[str] = None


class SinavSorusuResponse(SinavSorusuBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Öğrenci Sonuçları Schemas
class OgrenciSonucuBase(BaseModel):
    sinav_id: str
    ogrenci_id: str
    soru_no: int
    ogrenci_cevabi: Optional[str] = None


class OgrenciSonucuCreate(OgrenciSonucuBase):
    pass


class OgrenciSonucuResponse(OgrenciSonucuBase):
    id: int
    bert_skoru: Optional[float] = None
    llm_skoru: Optional[float] = None
    final_puan: Optional[float] = None
    yorum: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Puanlama Request
class PuanlamaRequest(BaseModel):
    sinav_id: str
    ogrenci_id: str
    soru_no: int
    ogrenci_cevabi: str


class PuanlamaResponse(BaseModel):
    bert_skoru: float
    llm_skoru: float
    yorum: str


# Raporlama Schemas
class ReportItem(BaseModel):
    soru_no: int
    soru_metni: Optional[str] = ""
    ogrenci_cevabi: Optional[str] = ""
    final_puan: Optional[float] = 0.0
    # Rubrikteki soru agirligi / bu sorunun sinavdaki maksimum puani (Orn: 30, 70)
    max_puan: Optional[float] = 100.0
    yorum: Optional[str] = ""

class ReportRequest(BaseModel):
    request_id: str
    results: List[ReportItem]
