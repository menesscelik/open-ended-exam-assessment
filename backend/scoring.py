"""
Hybrid Scoring Module
Combines BERTurk similarity (SBERT) with Ollama (Local LLM) analysis
"""

import logging
import json
import re
import os
from google import genai
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
current_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(current_dir, '.env'))

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    logger.error("GOOGLE_API_KEY not found in environment variables!")

def get_gemini_client():
    return genai.Client(api_key=api_key)


def analyze_with_gemini(ideal_cevap: str, ogrenci_cevabi: str, soru_metni: str = "", answer_key_text: str = None, rubric_text: str = None, bert_score: float = 0.0) -> dict:
    import time
    import random

    max_retries = 3
    base_delay = 5  # seconds

    for attempt in range(max_retries + 1):
        try:
            client = get_gemini_client()
            
            # Determine sources
            source_key = f"""
        1) CEVAP ANAHTARI (ANSWER_KEY_TEXT):
        {answer_key_text if answer_key_text else ideal_cevap}
        (Bu metin, değerlendirmede birincil doğruluk kaynağıdır.)"""

            source_rubric = f"""
        2) RUBRİK (RUBRIC_TEXT):
        {rubric_text if rubric_text else '''
        - Kavramsal Doğruluk: Anahtar kelimeler ve temel kavramlar.
        - Mantıksal Tutarlılık: İfadelerin tutarlılığı.
        - Kapsam ve Detay
        - Terminoloji ve İfade
        '''}"""

            prompt = f"""ROL: Akademik sınav değerlendiricisisin.

        GİRDİLER:
        SORU: {soru_metni if soru_metni else 'Belirtilmedi'}
        ÖĞRENCİ CEVABI: {ogrenci_cevabi}
        
        KAYNAKLAR:
        {source_key}
        {source_rubric}

        EK BİLGİ:
        - SBERT Benzerlik Skoru: %{bert_score:.1f} (Referans amaçlı)

        GÖREV:
        1. Öğrenci cevabını SADECE verilen rubrik ve cevap anahtarındaki puanlama ölçeğine göre puanla.
        2. ASLA 100 üzerinden puanlama yapma (eğer sorunun kendi puanı 100 değilse).
        3. Sorunun puan değeri (Örn: "10 Puan", "15 Puan") metinlerde varsa, "soru_max_puan" olarak onu kullan.
        4. Eğer sorunun puanı yazmıyorsa, rubrikteki kriterlerin puanlarını topla ve bu toplamı "soru_max_puan" olarak kabul et.
        5. Rubrikteki her kriteri değerlendir.

        ÇIKTI FORMATI (JSON):
        {{
          "kriterler": [
            {{
                "kriter_adi": "Kriter Adı",
                "puan": <verilen_puan>,
                "max_puan": <kriter_max_puan>,
                "durum": "TAM/KISMEN/YOK",
                "gerekce": "Kısa açıklama"
            }}
          ],
          "toplam_puan": <toplam_puan>,
          "soru_max_puan": <max_puan_rubrik_toplami>,
          "genel_yorum": "Öğrenci cevabına yönelik akademik geri bildirim."
        }}
        """
            
            # Using gemini-flash-latest to match OCR model
            response = client.models.generate_content(
                model='gemini-flash-latest',
                contents=prompt,
                config={
                    'response_mime_type': 'application/json'
                }
            )
            
            result = json.loads(response.text)
            
            llm_skoru = float(result.get('toplam_puan', 0))
            max_puan = float(result.get('soru_max_puan', 0)) # Default to 0 to trigger summation logic
            genel_yorum = result.get('genel_yorum', '')
            kriterler = result.get('kriterler', [])
            
            # Calculate max safe score from criteria
            sum_criteria_max = 0
            if kriterler:
                for k in kriterler:
                    try:
                        sum_criteria_max += float(k.get('max_puan', 0))
                    except: pass
            
            # Logic to enforce rubric max score
            # If the model returned 100 or 0, but we have criteria sum, use criteria sum.
            # If model returned a specific number (e.g. 15) that matches criteria sum, keep it.
            if sum_criteria_max > 0:
                if max_puan == 0 or max_puan == 100:
                     max_puan = sum_criteria_max
                elif max_puan != sum_criteria_max:
                    # Trust the explicit criteria sum over the hallucinated max_puan if they differ significantly
                    # unless max_puan is clearly stated in the prompt context (hard to valid check via code alone)
                    # For safety, we prefer the sum of components.
                    logger.info(f"Mismatch in max_puan ({max_puan}) vs criteria sum ({sum_criteria_max}). Using sum.")
                    max_puan = sum_criteria_max

            # Fallback if everything fails
            if max_puan == 0:
                max_puan = 100

            logger.info(f"Gemini analysis complete (Question Score): {llm_skoru}/{max_puan}")
            
            return {
                'llm_skoru': llm_skoru,
                'max_puan': max_puan,
                'yorum': genel_yorum
            }
                
        except Exception as e:
            error_msg = str(e)
            # Retry on Rate Limits (429) AND Internal Errors (500)
            # Retry on Rate Limits (429) AND Internal Errors (500)
            if "500" in error_msg or "INTERNAL" in error_msg:
                wait_time = 20
                logger.warning(f"Internal Server Error (500). Retrying in {wait_time}s... (Attempt {attempt+1}/{max_retries})")
                time.sleep(wait_time)
                continue
            elif "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                wait_time = base_delay * (2 ** attempt) + random.uniform(0, 1)
                logger.warning(f"Rate limit hit. Retrying in {wait_time:.2f}s... (Attempt {attempt+1}/{max_retries})")
                time.sleep(wait_time)
                continue
            else:
                logger.error(f"Gemini analysis failed: {e}")
                return {
                    'llm_skoru': 0.0,
                    'max_puan': 100, # Default to 100 on hard error
                    'yorum': f"Analiz hatası (Gemini): {str(e)}"
                }
    
    # If loops ends without success
    return {
        'llm_skoru': 0.0,
        'max_puan': 100,
        'yorum': "Hata: API kotası aşıldı (429 Rate Limit). Lütfen biraz bekleyip tekrar deneyin."
    }


def calculate_final_score(bert_skoru: float, llm_skoru: float, max_puan: float = 100.0) -> float:
    """
    Returns the LLM calculated score, respecting the max_puan limit.
    """
    final_puan = llm_skoru
    final_puan = max(0, min(max_puan, final_puan))
    return round(final_puan, 2)


def evaluate_answer(
    ideal_cevap: str, 
    ogrenci_cevabi: str, 
    soru_metni: str = "",
    anahtar_kelimeler: str = "",
    answer_key_text: str = None,
    rubric_text: str = None
) -> dict:
    """
    Complete evaluation pipeline: SBERT Similarity + Ollama Analysis
    """
    from similarity import calculate_bert_score, calculate_keyword_score
    
    # Step 1: Calculate BERT similarity
    reference_text = ideal_cevap if ideal_cevap else (answer_key_text if answer_key_text else "")
    
    bert_skoru = calculate_bert_score(reference_text, ogrenci_cevabi)
    bert_percentage = bert_skoru * 100
    
    # Step 2: Get Gemini analysis
    gemini_result = analyze_with_gemini(ideal_cevap, ogrenci_cevabi, soru_metni, answer_key_text, rubric_text, bert_score=bert_percentage)
    llm_skoru = gemini_result['llm_skoru']
    max_puan = gemini_result.get('max_puan', 100)
    yorum = gemini_result['yorum']
    
    # Step 3: Calculate final
    final_puan = calculate_final_score(bert_percentage, llm_skoru, max_puan)
    
    if anahtar_kelimeler:
        keyword_score = calculate_keyword_score(anahtar_kelimeler, ogrenci_cevabi)
        if keyword_score < 0.5:
             yorum += f"\n\n(Not: Anahtar kelime eşleşmesi düşük: %{int(keyword_score*100)})"
    
    return {
        'bert_skoru': round(bert_skoru, 4), 
        'llm_skoru': round(llm_skoru, 2),
        'final_puan': final_puan,
        'max_puan': max_puan,
        'yorum': yorum
    }
