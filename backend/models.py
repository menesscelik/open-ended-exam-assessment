"""
Database Models
SQLAlchemy ORM models for exam system
"""

from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from database import Base


class SinavSorulari(Base):
    """Sınav Soruları Tablosu - Exam Questions Table"""
    __tablename__ = "sinav_sorulari"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    sinav_id = Column(String(50), nullable=False, index=True)  # Exam identifier
    soru_no = Column(Integer, nullable=False)  # Question number
    soru_metni = Column(Text, nullable=False)  # Question text
    ideal_cevap = Column(Text, nullable=False)  # Ideal answer
    anahtar_kelimeler = Column(Text, nullable=True)  # Keywords (comma separated)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())


class OgrenciSonuclari(Base):
    """Öğrenci Sonuçları Tablosu - Student Results Table"""
    __tablename__ = "ogrenci_sonuclari"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    sinav_id = Column(String(50), nullable=False, index=True)
    ogrenci_id = Column(String(50), nullable=False, index=True)
    soru_no = Column(Integer, nullable=False)
    ogrenci_cevabi = Column(Text, nullable=True)  # Student's answer
    bert_skoru = Column(Float, nullable=True)  # BERTurk similarity score (0-1)
    llm_skoru = Column(Float, nullable=True)  # Gemini logic score (0-100)
    final_puan = Column(Float, nullable=True)  # Final calculated score
    yorum = Column(Text, nullable=True)  # Gemini feedback/comment
    created_at = Column(DateTime, server_default=func.now())
