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
import cv2
import easyocr
import numpy as np

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


# Initialize EasyOCR reader once (global) to avoid loading model on every request
# We use Turkish and English
try:
    # Use GPU if available (auto-detect)
    reader = easyocr.Reader(['tr', 'en'], gpu=True) 
    logger.info("EasyOCR model loaded successfully (GPU enabled if available).")
except Exception as e:
    logger.error(f"Failed to load EasyOCR: {e}")
    reader = None

def anonymize_student_data_local(image: Image.Image) -> tuple[Image.Image, dict]:
    """
    Detects 'Adı', 'Soyadı', 'Numara' fields using EasyOCR,
    extracts the text next to them (value), and then redacts that area.
    
    Returns:
        (redacted_image, extracted_data_dict)
    """
    extracted_data = {}
    
    if reader is None:
        logger.warning("EasyOCR reader not available. Skipping anonymization.")
        return image, extracted_data
        
    try:
        # Convert PIL to Numpy (RGB)
        open_cv_image = np.array(image.convert("RGB")) 
        
        img_h, img_w, _ = open_cv_image.shape
        
        # DEFINITION: Only look at top 25% of the page for student info header
        header_limit = int(img_h * 0.25)
        
        # EasyOCR works with numpy array
        # Get all text blocks on the page (or at least the top part if we cropped, but here we pass full)
        results = reader.readtext(open_cv_image)
        
        # Convert to BGR for OpenCV drawing
        overlay = open_cv_image[:, :, ::-1].copy()
        
        # Strict keywords as requested by user
        keywords = ['adi', 'adı', 'soyadi', 'soyadı', 'numara', 'no', 'ad', 'soyad', 'ogrenci']
        
        matches_found = []

        for (bbox, text, prob) in results:
            y_min = int(bbox[0][1])
            x_min = int(bbox[0][0])
            
            # CRITICAL CHECK: Ignore anything below the header limit
            if y_min > header_limit:
                continue
                
            text_lower = text.lower().strip()
            
            matched = False
            for k in keywords:
                if k in text_lower:
                    matched = True
                    break
            
            if matched:
                matches_found.append({
                    'bbox': bbox,
                    'text': text,
                    'y': y_min,
                    'x': x_min
                })

        # Sort matches by Y (top to bottom), then X (left to right)
        matches_found.sort(key=lambda item: (item['y'], item['x']))
        
        # Limit to likely fields (Ad Soyad, Numara)
        # We try to be smart: if we find multiple, we redact them.
        # But we explicitly want to capture Name and Number.
        matches_to_redact = matches_found[:2] # Limited to strictly 2 as requested
        
        for match in matches_to_redact:
            bbox = match['bbox']
            label_text = match['text']
            
            x_min = int(bbox[0][0])
            y_min = int(bbox[0][1])
            x_max = int(bbox[2][0])
            y_max = int(bbox[2][1])
            
            w = x_max - x_min
            h = y_max - y_min
            
            # Define Redaction Zone (To the right of the label)
            redact_x = x_max + 5
            redact_y = y_min - 5
            redact_h = h + 10 
            
            if 'no' in label_text.lower() or 'numara' in label_text.lower():
                redact_w = 300 
                key_type = "number"
            else:
                redact_w = 500 
                key_type = "name"
                
            if redact_x + redact_w > img_w:
                redact_w = img_w - redact_x
            
            redaction_rect = (redact_x, redact_y, redact_x + redact_w, redact_y + redact_h)
            
            # --- EXTRACTION STEP ---
            # Define valid X range for this label
            # Start: Right edge of current label
            # End: Left edge of the NEXT label on the same line (if any), or Page Width
            
            valid_x_start = x_max
            valid_x_end = img_w
            
            # Find closest label to the right on the same line
            for other_match in matches_to_redact:
                if other_match['bbox'] == bbox: continue
                
                other_y_center = (other_match['bbox'][0][1] + other_match['bbox'][2][1]) / 2
                label_y_center = (bbox[0][1] + bbox[2][1]) / 2
                
                # Check if on same line
                if abs(other_y_center - label_y_center) < (h * 1.5):
                     other_x_min = other_match['bbox'][0][0]
                     # If it is to the right of current label
                     if other_x_min > x_max:
                         # Update valid_x_end if this label is closer than current valid_x_end
                         if other_x_min < valid_x_end:
                             valid_x_end = other_x_min

            found_values = []
            
            for (r_bbox, r_text, r_prob) in results:
                if r_bbox == bbox: continue
                
                r_x_min = r_bbox[0][0]
                r_x_max = r_bbox[2][0]
                r_y_center = (r_bbox[0][1] + r_bbox[2][1]) / 2
                label_y_center = (bbox[0][1] + bbox[2][1]) / 2

                # 1. Check Vertical Alignment (Same Line)
                if abs(r_y_center - label_y_center) > (h * 1.2): 
                    continue

                # 2. Check Horizontal Alignment (Strictly within valid range)
                # Text must start AFTER the label ends
                # Text must start BEFORE the next label starts
                if r_x_min > valid_x_start and r_x_min < valid_x_end:
                    found_values.append({
                        'text': r_text,
                        'x': r_x_min
                    })
            
            # Sort by X
            found_values.sort(key=lambda v: v['x'])
            extracted_value = " ".join([v['text'] for v in found_values]).strip()
            
            # Post-Processing: Filtering based on known types
            if key_type == "number":
                # If expecting number, filter out non-digit heavy strings if possible, 
                # but user might have written "No: 123", so we just keep it.
                # But if we accidentally grabbed a name, it's bad.
                # Let's rely on the geometric constraint above.
                pass
            
            if extracted_value:
                if key_type == "name" and "name" not in extracted_data:
                    extracted_data["name"] = extracted_value
                elif key_type == "number" and "number" not in extracted_data:
                     # Remove potential mistakenly captured text parts that are clearly not numbers?
                     # For now, trust the geometry.
                    extracted_data["number"] = extracted_value
            
                print(f"DEBUG: Extracted '{extracted_value}' for label '{label_text}' (Range: {valid_x_start}-{valid_x_end})")

            # --- REDACTION STEP ---
            cv2.rectangle(overlay, (redact_x, redact_y), (redact_x + redact_w, redact_y + redact_h), (0, 0, 0), -1)

        # Convert back to RGB and PIL
        result_image = cv2.cvtColor(overlay, cv2.COLOR_BGR2RGB)
        return Image.fromarray(result_image), extracted_data
        
    except Exception as e:
        logger.error(f"EasyOCR anonymization failed: {e}")
        return image, extracted_data


