"""
Hybrid Scoring Module
Combines BERTurk similarity (SBERT) with OpenAI GPT-4o-mini analysis
"""

import logging
import json
import re
import os
from openai import OpenAI
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
current_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(current_dir, '..', '..', '.env'))

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    logger.error("OPENAI_API_KEY not found in environment variables!")

def get_openai_client():
    return OpenAI(api_key=api_key)


def analyze_with_openai(ideal_cevap: str, ogrenci_cevabi: str, soru_metni: str = "", answer_key_text: str = None, rubric_text: str = None, bert_score: float = 0.0, soru_no: int = 1) -> dict:
    import time
    import random

    max_retries = 3
    base_delay = 5  # seconds

    for attempt in range(max_retries + 1):
        try:
            client = get_openai_client()
            
            # Determine sources
            source_key = f"""
        1) CEVAP ANAHTARI (ANSWER_KEY_TEXT):
        {answer_key_text if answer_key_text else ideal_cevap}
        (Bu metin, değerlendirmede birincil doğruluk kaynağıdır.)"""

            source_rubric = f"""
        2) RUBRİK (RUBRIC_TEXT):
        {rubric_text if rubric_text else 'Genel değerlendirme yap.'}"""

            system_prompt = f"""
    Sen, aşağıdaki "KESİN KURALLAR"a sıkı sıkıya bağlı kalarak sınav kağıdı okuyan profesyonel bir eğitimcisin.
    Amacın öğrencinin notunu bol keseden vermek DEĞİL, rubrikte belirtilen kriterlere göre kılı kırk yaran bir değerlendirme yapmaktır.
    """

            user_prompt = f"""
    ## BAĞLAM
    Değerlendirilen Soru Numarası: {soru_no}
    Soru Metni: "{soru_metni}"

    ## KAYNAKLAR
    {source_key}
    {source_rubric}

    ## ÖĞRENCİ CEVABI
    "{ogrenci_cevabi}"

    ## SBERT SEMANTİK SKORU: {bert_score:.2f}

    ## KESİN KURALLAR VE GÖREVLER (MUTLAKA UYULACAK)

    1. **PUAN AĞIRLIĞI TESPİTİ:**
       - Rubrik metnini incele ve SADECE "Soru {soru_no}" için belirlenmiş puan değerini (Ağırlığını) bul (Örn: "Soru {soru_no}: 30 Puan" veya "%30").
       - Eğer rubrikte soruya özel bir ağırlık yazıyorsa (Örn: 30), BU SORUNUN "max_puan" (soru_max_puan) değeri OLMALIDIR. 
       - Eğer rubrikte açıkça bir ağırlık yoksa, varsayılan olarak 100 kabul et.
       - "toplam_puan" ASLA bu ağırlığı geçemez. (Örn: Ağırlık 30 ise, öğrenci mükemmel de yazsa max 30 alır.)

    2. **KAVRAMSAL DOĞRULUK (HARD GATE):**
       - Öğrencinin cevabı temel kavramı yanlış tanımlıyorsa veya konuyla alakasız bir alandan bahsediyorsa (Örn: "Sentiment Analysis" bir görüntü işleme yöntemidir diyorsa):
         - **PUAN = 0**
         - Dil bilgisi, açıklık, yapı vb. için ASLA kısmi puan verme. Doğrudan 0 ver.
         - Yorumda "Kavramsal Doğruluk hatası nedeniyle puan verilmemiştir" diye belirt.

    3. **PUANLAMA MANTIĞI (ÖNEMLİ):**
       - **ANLAMSAL EŞDEĞERLİK ESASTIR:** Öğrencinin cevabı, kelime kelime Cevap Anahtarı ile aynı olmak zorunda değildir.
       - Eğer öğrenci farklı kelimelerle ifade etmiş olsa bile, **ANLAMSAL OLARAK (SEMANTİK) AYNI KAPIYA ÇIKIYORSA, aynı mantığı ve sonucu doğru bir şekilde veriyorsa TAM PUAN ver.**
       - Sadece ezberlenmiş anahtar kelimeleri arama; mantıksal kurguyu ve sonucun doğruluğunu puanla.
       - Ancak, kavramsal olarak yanlışsa (farklı bir şey anlatıyorsa) puan verme.
       - Varsa rubrikteki alt kırılımlara (Grammar, Clarity, vb.) bak.

    4. **ÇIKTI:**
       - JSON formatında çıktı ver.
       - Yorumların, neden puan kırdığını veya neden tam puan verdiğini RUBRİK maddelerine atıfta bulunarak açıklamalıdır.

    ## ÇIKTI FORMATI (JSON)
    {{
        "toplam_puan": (float) "Öğrencinin aldığı puan (Ağırlıklandırılmış, Örn: 15.0)",
        "soru_max_puan": (float) "Bu sorunun sınavdaki ağırlığı/maks puanı (Örn: 30.0)",
        "genel_yorum": "Rubrik dayanaklı geri bildirim.",
        "eksikler": ["Eksik 1", "Eksik 2"],
        "kriterler": [
            {{
                "kriter_tanimi": "Kriter Adı",
                "alinan_puan": (float),
                "max_puan": (float)
            }}
        ]
    }}
    """
            
            # Using GPT-4o-mini for cost-effective reasoning
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.0  # Zero temperature for strict rule following
            )
            
            result_text = response.choices[0].message.content
            result = json.loads(result_text)
            
            llm_skoru = float(result.get('toplam_puan', 0))
            max_puan = float(result.get('soru_max_puan', 0))
            genel_yorum = result.get('genel_yorum', '')
            kriterler = result.get('kriterler', [])

            # Logic to enforce rubric max score
            # If max_puan is 0 or 100, checking criteria sum might happen, but usually we trust LLM to find "30 points"
            if max_puan == 0:
                 max_puan = 100

            logger.info(f"GPT-4o-mini analysis complete (Q{soru_no}): {llm_skoru}/{max_puan}")
            
            return {
                'llm_skoru': llm_skoru,
                'max_puan': max_puan,
                'yorum': genel_yorum
            }
                
        except Exception as e:

            error_msg = str(e)
            if "500" in error_msg or "internal" in error_msg.lower():
                wait_time = 20
                logger.warning(f"Internal Server Error (500). Retrying in {wait_time}s... (Attempt {attempt+1}/{max_retries})")
                time.sleep(wait_time)
                continue
            elif "429" in error_msg or "rate limit" in error_msg.lower():
                wait_time = base_delay * (2 ** attempt) + random.uniform(0, 1)
                logger.warning(f"Rate limit hit. Retrying in {wait_time:.2f}s... (Attempt {attempt+1}/{max_retries})")
                time.sleep(wait_time)
                continue
            else:
                logger.error(f"OpenAI analysis failed: {e}")
                return {
                    'llm_skoru': 0.0,
                    'max_puan': 100, # Default to 100 on hard error
                    'yorum': f"Analiz hatası (GPT-4o-mini): {str(e)}"
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
    rubric_text: str = None,
    soru_no: int = 1
) -> dict:
    """
    Complete evaluation pipeline: SBERT Similarity + OpenAI Analysis
    """
    from app.services.similarity import calculate_bert_score, calculate_keyword_score
    
    # Step 1: Calculate BERT similarity
    # SBERT DISABLED TEMPORARILY AS PER USER REQUEST
    # reference_text = ideal_cevap if ideal_cevap else (answer_key_text if answer_key_text else "")
    # bert_skoru = calculate_bert_score(reference_text, ogrenci_cevabi)
    # bert_percentage = bert_skoru * 100
    bert_skoru = 0.0
    bert_percentage = 0.0
    
    # Step 2: Get OpenAI analysis
    openai_result = analyze_with_openai(ideal_cevap, ogrenci_cevabi, soru_metni, answer_key_text, rubric_text, bert_score=bert_percentage, soru_no=soru_no)
    llm_skoru = openai_result['llm_skoru']
    max_puan = openai_result.get('max_puan', 100)
    yorum = openai_result['yorum']
    
    # Step 3: Calculate final
    # Ensure max_puan is valid
    if max_puan <= 0:
        max_puan = 100.0
        
    final_puan = calculate_final_score(bert_percentage, llm_skoru, max_puan)
    
    # SAFETY CHECK REMOVED AS PER USER REQUEST
    # The user wants to rely on semantic evaluation by the LLM, not strict vector similarity.
    # if bert_percentage < 20.0 and llm_skoru > (max_puan * 0.4):
    #     logger.warning(f"Suspicious Score Detected! SBERT: {bert_percentage}%, LLM: {llm_skoru}/{max_puan}. Forcing reduction.")
    #     final_puan = 0.0
    #     llm_skoru = 0.0
    #     yorum += "\\n\\n⚠️ (DÜZELTME: Cevabınızın anlamsal benzerlik skoru çok düşük olduğu için...)"

    if anahtar_kelimeler:
        keyword_score = calculate_keyword_score(anahtar_kelimeler, ogrenci_cevabi)
        if keyword_score < 0.5:
             yorum += f"\\n\\n(Not: Anahtar kelime eşleşmesi düşük: %{int(keyword_score*100)})"
    
    return {
        'bert_skoru': round(bert_skoru, 4), 
        'llm_skoru': round(llm_skoru, 2),
        'final_puan': final_puan,
        'max_puan': max_puan,
        'yorum': yorum
    }
