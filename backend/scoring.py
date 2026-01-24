"""
Hybrid Scoring Module
Combines BERTurk similarity (SBERT) with Ollama (Local LLM) analysis
"""

import logging
import json
import re
import requests

logger = logging.getLogger(__name__)

# Ollama Configuration
OLLAMA_API_URL = "http://127.0.0.1:11434/api/generate"
# Using deepseek-r1:8b as requested/available
OLLAMA_MODEL = "deepseek-r1:14b"


def analyze_with_ollama(ideal_cevap: str, ogrenci_cevabi: str, soru_metni: str = "", answer_key_text: str = None, rubric_text: str = None, bert_score: float = 0.0) -> dict:
    """
    Analyze student answer using local Ollama model (DeepSeek R1).
    """
    try:
        # Determine sources
        source_key = f"""
    1) CEVAP ANAHTARI (ANSWER_KEY_TEXT):
    {answer_key_text if answer_key_text else ideal_cevap}
    (Bu metin, değerlendirmede birincil doğruluk kaynağıdır.)"""

        source_rubric = f"""
    2) RUBRİK (RUBRIC_TEXT):
    {rubric_text if rubric_text else '''
    - Kavramsal Doğruluk (40 Puan): Cevap, anahtar kelimeleri ve temel kavramları içeriyor mu?
    - Mantıksal Tutarlılık (30 Puan): İfadeler kendi içinde tutarlı ve soruyla alakalı mı?
    - Kapsam ve Detay (20 Puan): Cevap anahtarındaki kritik noktaların tamamına değinilmiş mi?
    - Terminoloji ve İfade (10 Puan): Akademik dil ve doğru terminoloji kullanılmış mı?
    '''}"""

        prompt = f"""ROL TANIMI:
    Sen, açık uçlu sınav cevaplarını rubrik tabanlı ve anlamsal değerlendiren akademik bir yapay zeka sistemisin.

    SİSTEM ÇALIŞMA PRENSİBİ:
    - Rubrik, puan dağılımını ve değerlendirme kriterlerini tanımlar.
    - Semantik analiz (SBERT + Sen), her rubrik kriterinin öğrenci cevabında anlamsal olarak karşılanıp karşılanmadığını belirler.
    - SBERT bağımsız bir puan değildir, sadece yardımcı bir araçtır.

    DEĞERLENDİRME KAYNAKLARI:
    {source_key}
    {source_rubric}

    EK SİNYALLER:
    - Hesaplanan SBERT Benzerlik Skoru: %{bert_score:.1f}
      (Bu skor, öğrenci cevabının cevap anahtarına genel kelime benzerliğini gösterir. Düşükse bile anlam eşdeğer olabilir, dikkatli ol.)

    ÖĞRENCİ CEVABI:
    {ogrenci_cevabi}

    SORU BAĞLAMI:
    {soru_metni if soru_metni else 'Belirtilmedi'}

    DEĞERLENDİRME ADIMLARI (ZORUNLU):
    1. Rubrikte yer alan her kriteri ayrı ayrı ele al.
    2. Her kriter için sor: "Öğrenci cevabı, bu kriterin gerektirdiği anlamı karşılıyor mu?"
    3. Kelime eşleşmesi arama. Aynı anlama gelen ifadeleri TAM karşılanmış say.
    4. Her kriter için anlamsal karşılama durumunu belirle:
       - TAM karşılıyor → %100 (Kriter puanının tamamı)
       - KISMEN karşılıyor → %50-80 (Kriter puanının bir kısmı)
       - KARŞILAMIYOR → %0-30 (Puan yok veya çok az)
    5. Kriter puanı = (Karşılama Oranı) × (Kriter Max Puanı)
    6. Tüm kriter puanlarını topla → Nihai Puan.

    ÖZEL KURALLAR:
    - Yazım farkları ve terminoloji değişiklikleri anlamı bozmuyorsa ceza sebebi değildir.
    - Rubrikte yer almayan hiçbir beklenti ekleme.
    - Semantik benzerlik yüzdesini DOĞRUDAN final puana ekleme, sadece karar verirken destek al.

    ÇIKTI FORMATI (JSON):
    {{
      "kriterler": [
        {{
            "kriter_adi": "Kavramsal Doğruluk",
            "durum": "TAM/KISMEN/YOK",
            "puan": <verilen_puan>,
            "max_puan": <kriter_max_puani>,
            "gerekce": "..."
        }},
        ... diğer kriterler
      ],
      "toplam_puan": <0-100 arası tamsayı - kriterlerin toplamı>,
      "genel_yorum": "<Tüm değerlendirmeyi özetleyen kısa akademik yorum>"
    }}
    
    Lütfen sadece yukarıdaki JSON formatında yanıt ver.
    """

        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1  # Low temperature for more deterministic/factual output
            }
        }

        logger.info(f"Sending request to Ollama ({OLLAMA_MODEL})...")
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=300)
        
        if response.status_code != 200:
            logger.error(f"Ollama API error: {response.text}")
            return {'llm_skoru': 50.0, 'yorum': f"Ollama hatası: {response.status_code}"}
            
        response_data = response.json()
        response_text = response_data.get("response", "")
        
        # Clean up <think> tags if DeepSeek includes them despite instructions
        response_text = re.sub(r'<think>.*?</think>', '', response_text, flags=re.DOTALL).strip()
        
        # Try to parse JSON
        try:
            cleaned_text = response_text.strip()
            
            # Remove markdown code blocks (backticks or single quotes)
            # Handle ```json ... ```, ``` ... ```, '''json ... ''', ''' ... '''
            cleaned_text = re.sub(r'[`\']{3}(?:json)?\s*(.*?)\s*[`\']{3}', r'\1', cleaned_text, flags=re.DOTALL)
            
            # Find JSON block using regex - look for the first { and the last }
            json_match = re.search(r'\{.*\}', cleaned_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                result = json.loads(json_str)
                
                # New Format Parsing
                llm_skoru = float(result.get('toplam_puan', result.get('puan', 50))) # Fallback to old key just in case
                genel_yorum = result.get('genel_yorum', result.get('yorum', ''))
                kriterler = result.get('kriterler', [])
                
                # Format detailed feedback
                formatted_feedback = genel_yorum
                if kriterler:
                    formatted_feedback += "\n\nKRİTER DETAYLARI:\n"
                    for k in kriterler:
                        k_adi = k.get('kriter_adi', 'Kriter')
                        k_puan = k.get('puan', 0)
                        k_max = k.get('max_puan', '?')
                        k_gerekce = k.get('gerekce', '')
                        formatted_feedback += f"- **{k_adi}**: {k_puan}/{k_max} ({k.get('durum', '')}) - {k_gerekce}\n"
                    
                logger.info(f"Ollama analysis complete: score={llm_skoru}")
                return {
                    'llm_skoru': max(0, min(100, llm_skoru)),
                    'yorum': formatted_feedback
                }
            else:
                logger.warning("Could not find JSON in Ollama response")
                return {'llm_skoru': 50.0, 'yorum': response_text}
                
        except json.JSONDecodeError:
            logger.error("Failed to decode JSON from Ollama")
            return {'llm_skoru': 50.0, 'yorum': response_text}
            
    except requests.exceptions.ConnectionError:
        logger.error("Could not connect to Ollama. Is it running?")
        return {
            'llm_skoru': 0.0,
            'yorum': "Hata: Ollama servisine bağlanılamadı. Lütfen Ollama'nın çalıştığından emin olun (http://localhost:11434)."
        }
    except Exception as e:
        logger.error(f"Ollama analysis failed: {e}")
        return {
            'llm_skoru': 0.0,
            'yorum': f"Analiz hatası: {str(e)}"
        }


def calculate_final_score(bert_skoru: float, llm_skoru: float) -> float:
    """
    Calculate final score based on Strict Rubric-Based Semantic Evaluation.
    
    In this new system:
    - The LLM calculates the score by summing the points of satisfied rubric criteria.
    - SBERT is a helper signal (used inside the prompt context if needed), NOT an independent additive score.
    - Therefore, this function simply returns the LLM-calculated rubric score.
    
    Args:
        bert_skoru: Score between 0-100 (Logged for reference/debugging)
        llm_skoru: Score between 0-100 (The Rubric Sum calculated by LLM)
    """
    
    logger.info(f"Finalizing Score. LLM (Rubric Sum): {llm_skoru}, SBERT (Ref): {bert_skoru}")
    
    # User Rule: "Semantik benzerlik yuzdesini DOGRUDAN final puana ekleme."
    # The final score is purely the satisfaction of Rubric criteria as judged by the system.
    final_puan = llm_skoru
        
    final_puan = max(0, min(100, final_puan))
    
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
    
    # Step 1: Calculate BERT similarity (SBERT works offline)
    # If we have a massive answer key text, SBERT might be noisy against specific student answer
    # Ideally we should compare student answer to relevant part of Key.
    # For now, if we have specific 'ideal_cevap' (per question), use that.
    # If not, use the full Answer Key (might be suboptimal but better than nothing).
    reference_text = ideal_cevap if ideal_cevap else (answer_key_text if answer_key_text else "")
    
    bert_skoru = calculate_bert_score(reference_text, ogrenci_cevabi)
    # Convert 0-1 score to 0-100 percentage for consistency in logs/thought
    bert_percentage = bert_skoru * 100
    
    # Step 2: Get Ollama analysis (Logic & Missing parts)
    # Pass SBERT score as context
    ollama_result = analyze_with_ollama(ideal_cevap, ogrenci_cevabi, soru_metni, answer_key_text, rubric_text, bert_score=bert_percentage)
    llm_skoru = ollama_result['llm_skoru']
    yorum = ollama_result['yorum']
    
    # Step 3: Calculate final score
    final_puan = calculate_final_score(bert_percentage, llm_skoru)
    
    # Optional: Add keyword info
    if anahtar_kelimeler:
        keyword_score = calculate_keyword_score(anahtar_kelimeler, ogrenci_cevabi)
        if keyword_score < 0.5:
             yorum += f"\n\n(Not: Anahtar kelime eşleşmesi düşük: %{int(keyword_score*100)})"
    
    return {
        'bert_skoru': round(bert_skoru, 4),  # Keep as 0-1 for frontend display consistency if needed, or update frontend
        'llm_skoru': round(llm_skoru, 2),
        'final_puan': final_puan,
        'yorum': yorum
    }
