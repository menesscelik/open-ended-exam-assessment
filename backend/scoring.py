"""
Hybrid Scoring Module
Combines BERTurk similarity with Gemini LLM analysis
"""

import logging
import json
import re
import google.generativeai as genai

logger = logging.getLogger(__name__)

# Configure Gemini with hardcoded API key
api_key = "AIzaSyAUVkzhtCfRmKYpSVOeejRCSs_74mPVqF4"
genai.configure(api_key=api_key)


def get_gemini_model():
    """Returns the configured Gemini model for scoring."""
    return genai.GenerativeModel('gemini-flash-latest')


def analyze_with_gemini(ideal_cevap: str, ogrenci_cevabi: str, soru_metni: str = "") -> dict:
    """
    Analyze student answer using Gemini LLM.
    
    Args:
        ideal_cevap: The ideal/expected answer
        ogrenci_cevabi: The student's answer
        soru_metni: Optional question text for context
        
    Returns:
        dict with 'llm_skoru' (0-100) and 'yorum' (feedback text)
    """
    try:
        model = get_gemini_model()
        
        prompt = f"""Sen bir sınav değerlendirme asistanısın. Aşağıdaki öğrenci cevabını ideal cevapla karşılaştır ve değerlendir.

{"Soru: " + soru_metni if soru_metni else ""}

İdeal Cevap:
{ideal_cevap}

Öğrenci Cevabı:
{ogrenci_cevabi}

Lütfen şunları yap:
1. Öğrenci cevabının teknik doğruluğunu değerlendir
2. Eksik veya yanlış noktaları belirle
3. 0-100 arası bir puan ver

Çıktını SADECE aşağıdaki JSON formatında ver, başka bir şey yazma:
{{"puan": <0-100 arası sayı>, "yorum": "<kısa değerlendirme ve geri bildirim>"}}
"""
        
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Parse JSON response
        # Try to extract JSON from response
        json_match = re.search(r'\{[^}]+\}', response_text)
        if json_match:
            result = json.loads(json_match.group())
            llm_skoru = float(result.get('puan', 50))
            yorum = result.get('yorum', 'Değerlendirme yapıldı.')
        else:
            # Fallback parsing
            llm_skoru = 50.0
            yorum = response_text[:500]
        
        # Clamp score to valid range
        llm_skoru = max(0, min(100, llm_skoru))
        
        logger.info(f"Gemini analysis complete: score={llm_skoru}")
        return {
            'llm_skoru': llm_skoru,
            'yorum': yorum
        }
        
    except Exception as e:
        logger.error(f"Gemini analysis failed: {e}")
        return {
            'llm_skoru': 50.0,
            'yorum': f'Otomatik değerlendirme yapılamadı: {str(e)}'
        }


def calculate_final_score(bert_skoru: float, llm_skoru: float) -> float:
    """
    Calculate hybrid final score using the formula:
    Final Puan = (BERTurk Benzerlik × 40) + (LLM Mantık Puanı × 0.6)
    
    Args:
        bert_skoru: BERT similarity score (0-1)
        llm_skoru: Gemini logic score (0-100)
        
    Returns:
        Final score (0-100)
    """
    # Formula: (BERT × 40) + (LLM × 0.6)
    # BERT contribution: 0-40 points
    # LLM contribution: 0-60 points
    bert_contribution = bert_skoru * 40
    llm_contribution = llm_skoru * 0.6
    
    final_puan = bert_contribution + llm_contribution
    
    # Clamp to 0-100 range
    final_puan = max(0, min(100, final_puan))
    
    logger.info(f"Final score: BERT({bert_skoru:.2f}×40={bert_contribution:.1f}) + LLM({llm_skoru:.1f}×0.6={llm_contribution:.1f}) = {final_puan:.1f}")
    
    return round(final_puan, 2)


def evaluate_answer(
    ideal_cevap: str, 
    ogrenci_cevabi: str, 
    soru_metni: str = "",
    anahtar_kelimeler: str = ""
) -> dict:
    """
    Complete evaluation pipeline combining BERT and Gemini.
    
    Args:
        ideal_cevap: The ideal/expected answer
        ogrenci_cevabi: The student's answer
        soru_metni: Optional question text
        anahtar_kelimeler: Optional comma-separated keywords
        
    Returns:
        dict with bert_skoru, llm_skoru, final_puan, yorum
    """
    from similarity import calculate_bert_score, calculate_keyword_score
    
    # Step 1: Calculate BERT similarity
    bert_skoru = calculate_bert_score(ideal_cevap, ogrenci_cevabi)
    
    # Step 2: Get Gemini analysis
    gemini_result = analyze_with_gemini(ideal_cevap, ogrenci_cevabi, soru_metni)
    llm_skoru = gemini_result['llm_skoru']
    yorum = gemini_result['yorum']
    
    # Step 3: Calculate final score
    final_puan = calculate_final_score(bert_skoru, llm_skoru)
    
    # Optional: Add keyword bonus info to comment
    if anahtar_kelimeler:
        keyword_score = calculate_keyword_score(anahtar_kelimeler, ogrenci_cevabi)
        if keyword_score < 0.5:
            yorum += f" (Anahtar kelime eşleşmesi: %{int(keyword_score*100)})"
    
    return {
        'bert_skoru': round(bert_skoru, 4),
        'llm_skoru': round(llm_skoru, 2),
        'final_puan': final_puan,
        'yorum': yorum
    }
