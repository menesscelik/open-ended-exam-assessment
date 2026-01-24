"""
OCR Utilities Module
Provides Google Gemini-based text extraction with Turkish language support
"""

from PIL import Image
import os
import logging
from google import genai
from dotenv import load_dotenv
import json

# Determine current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv(os.path.join(current_dir, '.env'))

# Configure Gemini with API key from environment
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    logger.error("GOOGLE_API_KEY not found in environment variables!")

def get_gemini_client():
    """Returns the configured Gemini client."""
    return genai.Client(api_key=api_key)

def extract_text_from_image(image: Image.Image, prompt: str = None) -> str:
    """
    Extract text from a PIL Image using Google Gemini Vision API.
    
    Args:
        image: PIL Image object
        prompt: Optional custom prompt. If None, uses default Turkish OCR prompt.
        
    Returns:
        Structured list of questions/answers or raw text string
    """
    try:
        client = get_gemini_client()
        
        if prompt is None:
            # Updated prompt for structured extraction
            prompt = (
                "Bu görseldeki sınav kağıdını incele ve tüm soruları ayrı ayrı tespit et. "
                "Her bir soru için şu bilgileri JSON formatında çıkar:\n"
                "1. 'soru_no': Soru numarası (yoksa 1'den başlayarak ver)\n"
                "2. 'soru_metni': Sorunun metni (sadece soru kısmı, cevap değil)\n"
                "3. 'ogrenci_cevabi': Öğrencinin el yazısıyla verdiği cevap metni\n\n"
                "Kurallar:\n"
                "- Sadece JSON listesi döndür: [{'soru_no': 1, 'soru_metni': '...', 'ogrenci_cevabi': '...'}, ...]\n"
                "- Markdown (```json ... ```) kullanma, sadece saf JSON ver.\n"
                "- Türkçe karakterlere dikkat et.\n"
                "- Cevap yoksa boş string ver."
            )
            
        response = client.models.generate_content(
            model='gemini-flash-latest',
            contents=[prompt, image]
        )
        text = response.text
        
        # Try to parse JSON output
        cleaned_text = text.strip()
        if cleaned_text.startswith('```json'):
            cleaned_text = cleaned_text[7:-3].strip()
        elif cleaned_text.startswith('```'):
            cleaned_text = cleaned_text[3:-3].strip()
            
        try:
            structured_data = json.loads(cleaned_text)
            logger.info("Gemini returned valid structured JSON")
            return structured_data
        except json.JSONDecodeError:
            logger.warning("Gemini did not return valid JSON, falling back to raw text")
            return text.strip()
        
    except Exception as e:
        logger.error(f"Gemini OCR failed: {e}")
        raise Exception(f"Google Gemini ile metin okunamadı: {str(e)}")

def normalize_text(text: str) -> str:
    """
    Normalize text - kept for backward compatibility if raw text is returned.
    """
    if not isinstance(text, str):
        return text  # Return as-is if it's already a list/dict
        
    if not text:
        return ""
    
    lines = text.split('\n')
    lines = [" ".join(line.split()) for line in lines]
    text = '\n'.join(lines)
    
    return text

def process_image_ocr(image: Image.Image, debug_dir: str = None, prompt: str = None) -> dict:
    """
    Complete OCR processing pipeline using Gemini.
    Can return either structured JSON (list) or raw text compatibility object.
    """
    processing_steps = []
    
    try:
        # Step 1: Send to Google Gemini
        processing_steps.append({
            'step': 1,
            'name': 'Google Gemini API',
            'description': 'Görsel işleniyor ve sorular ayrıştırılıyor',
            'status': 'in_progress'
        })
        
        result = extract_text_from_image(image, prompt=prompt)
        
        processing_steps[0]['status'] = 'completed'
        processing_steps[0]['result'] = 'Veri başarıyla alındı'
        
        # Check if result is structured list
        if isinstance(result, list):
            return {
                'structured_data': result,  # New field for structured questions
                'raw_text': str(result),    # Kept for compatibility
                'normalized_text': str(result),
                'processing_steps': processing_steps
            }
        else:
            # Fallback for plain text
            normalized_text = normalize_text(result)
            return {
                'raw_text': result,
                'normalized_text': normalized_text,
                'processing_steps': processing_steps
            }
        
    except Exception as e:
        if processing_steps:
            processing_steps[-1]['status'] = 'failed'
            processing_steps[-1]['error'] = str(e)
            
        raise Exception(f"OCR İşlemi Başarısız: {str(e)}")
