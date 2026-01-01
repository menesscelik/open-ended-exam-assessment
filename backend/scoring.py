"""
Hybrid Scoring Module
Combines BERTurk similarity (SBERT) with Ollama (Local LLM) analysis
"""

import logging
import json
import re
import requests
import json

logger = logging.getLogger(__name__)

# Ollama Configuration
OLLAMA_API_URL = "http://127.0.0.1:11434/api/generate"
# Using deepseek-r1:8b as requested/available
OLLAMA_MODEL = "deepseek-r1:8b"


def analyze_with_ollama(ideal_cevap: str, ogrenci_cevabi: str, soru_metni: str = "") -> dict:
    """
    Analyze student answer using local Ollama model (DeepSeek R1).
    
    Args:
        ideal_cevap: The ideal/expected answer
        ogrenci_cevabi: The student's answer
        soru_metni: Optional question text for context
        
    Returns:
        dict with 'llm_skoru' (0-100) and 'yorum' (feedback text)
    """
    try:
        prompt = f"""Sen bir sınav değerlendirme asistanısın. Görevin öğrencinin cevabını analiz etmek ve EKSİK kısımları belirlemektir.

{'Soru: ' + soru_metni if soru_metni else ''}

İdeal Cevap (Referans):
{ideal_cevap}

Öğrenci Cevabı:
{ogrenci_cevabi}

Lütfen şu adımları izle:
1. Öğrenci cevabında, ideal cevaba göre EKSİK olan anahtar noktaları tespit et.
2. Öğrenci cevabında YANLIŞ bilgi varsa belirt.
3. Öğrenci cevabının ne kadar kapsamlı olduğunu 0 ile 100 arasında puanla.

Çıktını SADECE aşağıdaki JSON formatında ver, başka hiçbir metin veya düşünce zinciri (<think>...</think>) ekleme:
{{
  "puan": <0-100 arası sayı>,
  "eksik_kisimlar": ["Eksik nokta 1", "Eksik nokta 2"],
  "yorum": "<Genel değerlendirme ve varsa yanlışlar>"
}}
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
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=60)
        
        if response.status_code != 200:
            logger.error(f"Ollama API error: {response.text}")
            return {'llm_skoru': 50.0, 'yorum': f"Ollama hatası: {response.status_code}"}
            
        response_data = response.json()
        response_text = response_data.get("response", "")
        
        # Clean up <think> tags if DeepSeek includes them despite instructions
        response_text = re.sub(r'<think>.*?</think>', '', response_text, flags=re.DOTALL).strip()
        
        # Try to parse JSON
        try:
            # Find JSON block using regex in case there is extra text
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                result = json.loads(json_str)
                
                llm_skoru = float(result.get('puan', 50))
                eksikler = result.get('eksik_kisimlar', [])
                genel_yorum = result.get('yorum', '')
                
                # Format feedback
                formatted_feedback = genel_yorum
                if eksikler:
                    formatted_feedback += "\n\nEksik Noktalar:\n" + "\n".join([f"- {e}" for e in eksikler])
                    
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
    Calculate hybrid final score.
    Now relying more on LLM for logic and BERT for semantic coverage.
    """
    # Formula: (BERT * 40%) + (LLM * 60%)
    bert_contribution = bert_skoru * 40
    llm_contribution = llm_skoru * 0.6
    
    final_puan = bert_contribution + llm_contribution
    final_puan = max(0, min(100, final_puan))
    
    return round(final_puan, 2)


def evaluate_answer(
    ideal_cevap: str, 
    ogrenci_cevabi: str, 
    soru_metni: str = "",
    anahtar_kelimeler: str = ""
) -> dict:
    """
    Complete evaluation pipeline: SBERT Similarity + Ollama Analysis
    """
    from similarity import calculate_bert_score, calculate_keyword_score
    
    # Step 1: Calculate BERT similarity (SBERT works offline)
    bert_skoru = calculate_bert_score(ideal_cevap, ogrenci_cevabi)
    # Convert 0-1 score to 0-100 percentage for consistency in logs/thought
    bert_percentage = bert_skoru * 100
    
    # Step 2: Get Ollama analysis (Logic & Missing parts)
    ollama_result = analyze_with_ollama(ideal_cevap, ogrenci_cevabi, soru_metni)
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
