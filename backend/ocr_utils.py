"""
OCR Utilities Module
Provides Google Gemini-based text extraction with Turkish language support
"""

from PIL import Image
import os
import logging
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
current_dir = os.path.dirname(os.path.abspath(__file__))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Gemini with hardcoded API key
api_key = "AIzaSyAUVkzhtCfRmKYpSVOeejRCSs_74mPVqF4"
genai.configure(api_key=api_key)

def get_gemini_model():
    """Returns the configured Gemini model instance."""
    return genai.GenerativeModel('gemini-flash-latest')

def extract_text_from_image(image: Image.Image, prompt: str = None) -> str:
    """
    Extract text from a PIL Image using Google Gemini Vision API.
    
    Args:
        image: PIL Image object
        prompt: Optional custom prompt. If None, uses default Turkish OCR prompt.
        
    Returns:
        Extracted raw text as string
    """
    try:
        model = get_gemini_model()
        
        if prompt is None:
            prompt = (
                "Bu görseldeki yazıları oku ve metne dök. "
                "Her satırı ayrı bir satır olarak yaz. "
                "Görselde satır değiştiğinde çıktıda da \\n ile yeni satıra geç. "
                "Türkçe karakterlere (ç, ş, ğ, ü, ö, ı, İ) dikkat et. "
                "Sadece metni yaz, yorum ekleme."
            )
            
        response = model.generate_content([prompt, image])
        text = response.text
        
        logger.info(f"Gemini extracted {len(text)} characters")
        return text.strip()
        
    except Exception as e:
        logger.error(f"Gemini OCR failed: {e}")
        raise Exception(f"Google Gemini ile metin okunamadı: {str(e)}")

def normalize_text(text: str) -> str:
    """
    Normalize text - Gemini usually gives clean output, but we ensure consistency.
    """
    if not text:
        return ""
    
    # Basic normalization - preserve line breaks and Turkish characters
    # Remove extra whitespace within lines, but keep line breaks
    lines = text.split('\n')
    lines = [" ".join(line.split()) for line in lines]
    text = '\n'.join(lines)
    
    return text

def process_image_ocr(image: Image.Image, debug_dir: str = None) -> dict:
    """
    Complete OCR processing pipeline using Gemini.
    Maintains compatibility with frontend response structure.
    
    Args:
        image: PIL Image object
        debug_dir: Unused in Cloud OCR but kept for signature compatibility
        
    Returns:
        Dictionary with 'raw_text', 'normalized_text', and 'processing_steps'
    """
    processing_steps = []
    
    try:
        # Step 1: Send to Google Gemini
        processing_steps.append({
            'step': 1,
            'name': 'Google Gemini API',
            'description': 'Görsel Google sunucularına gönderiliyor ve işleniyor',
            'status': 'in_progress'
        })
        
        raw_text = extract_text_from_image(image)
        
        processing_steps[0]['status'] = 'completed'
        processing_steps[0]['result'] = 'Metin başarıyla alındı'
        
        # Step 2: Normalization
        processing_steps.append({
            'step': 2,
            'name': 'Metin Normalizasyonu',
            'description': 'Metin standart formata getiriliyor',
            'status': 'completed',
            'result': 'Tamamlandı'
        })
        
        normalized_text = normalize_text(raw_text)
        
        return {
            'raw_text': raw_text,
            'normalized_text': normalized_text,
            'processing_steps': processing_steps
        }
        
    except Exception as e:
        if processing_steps:
            processing_steps[-1]['status'] = 'failed'
            processing_steps[-1]['error'] = str(e)
            
        raise Exception(f"OCR İşlemi Başarısız: {str(e)}")
