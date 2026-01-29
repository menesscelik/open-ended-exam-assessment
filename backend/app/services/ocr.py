from PIL import Image
import os
import logging
import base64
import io
import json
import cv2
import easyocr
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv

# Determine current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv(os.path.join(current_dir, '..', '..', '.env'))

# Configure OpenAI client
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    logger.error("OPENAI_API_KEY not found in environment variables!")

def get_openai_client():
    """Returns the configured OpenAI client."""
    return OpenAI(api_key=api_key)

def encode_image_to_base64(image: Image.Image) -> str:
    """Converts a PIL Image to a base64 string."""
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def extract_text_from_image(image: Image.Image, prompt: str = None) -> str:
    """
    Extract text from a PIL Image using OpenAI GPT-4o (Vision).
    """
    import time
    import random

    max_retries = 3
    base_delay = 5

    for attempt in range(max_retries + 1):
        try:
            client = get_openai_client()
            base64_image = encode_image_to_base64(image)
            
            if prompt is None:
                prompt_text = (
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
            else:
                prompt_text = prompt

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt_text},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=4000
            )
            
            text = response.choices[0].message.content
            
            # Try to parse JSON output
            cleaned_text = text.strip()
            if cleaned_text.startswith('```json'):
                cleaned_text = cleaned_text[7:-3].strip()
            elif cleaned_text.startswith('```'):
                cleaned_text = cleaned_text[3:-3].strip()
                
            try:
                structured_data = json.loads(cleaned_text)
                logger.info("OpenAI GPT-4o returned valid structured JSON")
                return structured_data
            except json.JSONDecodeError:
                logger.warning("OpenAI GPT-4o did not return valid JSON, falling back to raw text")
                return text.strip()
            
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "rate limit" in error_msg.lower():
                if attempt < max_retries:
                    wait_time = base_delay * (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(f"Rate limit hit during OCR. Retrying in {wait_time:.2f}s... (Attempt {attempt+1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
            elif "500" in error_msg or "internal" in error_msg.lower():
                if attempt < max_retries:
                    wait_time = 20
                    logger.warning(f"Internal Server Error (500) during OCR. Retrying in {wait_time}s... (Attempt {attempt+1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
            
            # If it's not a retryable error or max retries reached
            logger.error(f"OpenAI OCR failed: {e}")
            raise Exception(f"OpenAI GPT-4o ile metin okunamadı (Hata: {str(e)})")

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
        
        # DEFINITION: Only look at top 35% of the page to be safe (increased from 25%)
        header_limit = int(img_h * 0.35)
        
        # EasyOCR works with numpy array
        results = reader.readtext(open_cv_image)
        
        # Convert to BGR for OpenCV drawing
        overlay = open_cv_image[:, :, ::-1].copy()
        
        # Keywords
        # Refined to include "ad soyad" composite to catch cases like "Ad Soyad: ..."
        name_keywords = ['ad soyad', 'adı soyadı', 'ogrenci adi', 'öğrenci adı', 'adi', 'adı', 'soyadi', 'soyadı', 'isim'] 
        number_keywords = ['numara', 'no', 'ogrenci no', 'number']
        
        all_matches = [] # All text blocks found
        found_labels = [] # Specifically label blocks

        for (bbox, text, prob) in results:
            y_min = int(bbox[0][1])
            x_min = int(bbox[0][0])
            x_max = int(bbox[2][0])
            y_max = int(bbox[2][1])
            
            item = {
                'text': text,
                'text_lower': text.lower().strip(),
                'bbox': bbox,
                'x_min': x_min,
                'x_max': x_max,
                'y_min': y_min,
                'y_max': y_max,
                'y_center': (y_min + y_max) / 2
            }
            
            all_matches.append(item)
            
            # Check if this block is a label header?
            if y_min < header_limit:
                is_name = any(k in item['text_lower'] for k in name_keywords)
                is_num = any(k in item['text_lower'] for k in number_keywords)
                
                # PRIORITIZE NUMBER: 'Ogrenci No' should be num, not name.
                if is_num:
                    item['type'] = 'num_label'
                    found_labels.append(item)
                elif is_name:
                    item['type'] = 'name_label'
                    found_labels.append(item)

        # Sort labels top-to-bottom, left-to-right
        found_labels.sort(key=lambda item: (item['y_min'], item['x_min']))
        
        # Process labels to extract values to their RIGHT
        processed_types = set()
        
        for label in found_labels:
            if label['type'] in processed_types:
                continue # Already found this type
                
            # Define Scan Zone
            # Start: label's right edge + margin
            scan_x_start = label['x_max']
            scan_y_center = label['y_center']
            scan_height_tolerance = (label['y_max'] - label['y_min']) * 0.8 # Allow some offset
            
            # End: Identify the start of the NEXT label on the same line to act as a barrier
            scan_x_end = img_w # Default to page edge
            
            for other_label in found_labels:
                if other_label == label: continue
                # If on same line approx
                if abs(other_label['y_center'] - scan_y_center) < scan_height_tolerance:
                    # If to the right
                    if other_label['x_min'] > scan_x_start:
                        # If closer than current limit
                        if other_label['x_min'] < scan_x_end:
                            scan_x_end = other_label['x_min']
            
            # Now Find Values in this Zone
            found_values = []
            for match in all_matches:
                if match == label: continue
                if match in found_labels and match['type'] == label['type']: continue # Skip self-similar labels
                
                # Check Vertical Alignment (Same Line)
                if abs(match['y_center'] - scan_y_center) < scan_height_tolerance:
                    # Check Horizontal Alignment
                    # Must be to the right of start
                    # Must be to the left of end
                    if match['x_min'] > scan_x_start and match['x_max'] <= scan_x_end: # lenient max check
                        found_values.append(match)
            
            # Sort found values left-to-right
            found_values.sort(key=lambda v: v['x_min'])
            
            extracted_text = " ".join([v['text'] for v in found_values]).strip()
            
            if extracted_text:
                if label['type'] == 'name_label':
                    cleaned_val = extracted_text.replace(':', '').strip()
                    extracted_data['name'] = cleaned_val
                    processed_types.add('name_label')
                    logger.info(f"Detected Name: {cleaned_val}")
                elif label['type'] == 'num_label':
                    cleaned_val = extracted_text.replace(':', '').strip()
                    extracted_data['number'] = cleaned_val
                    processed_types.add('num_label')
                    logger.info(f"Detected Number: {cleaned_val}")
            
            # --- REDACTION LOGIC ---
            # Redact the label AND the value found (or the empty space where it should be)
            # Redact label
            redact_margin = 5
            cv2.rectangle(overlay, 
                         (label['x_min'] - redact_margin, label['y_min'] - redact_margin), 
                         (label['x_max'] + redact_margin, label['y_max'] + redact_margin), 
                         (0, 0, 0), -1)
            
            # Redact value zone
            # If we found items, redact them. If not, redact a generic box to be safe.
            if found_values:
                # Redact from start of first value to end of last value
                val_x_min = found_values[0]['x_min']
                val_x_max = found_values[-1]['x_max']
                val_y_min = min([v['y_min'] for v in found_values])
                val_y_max = max([v['y_max'] for v in found_values])
                
                cv2.rectangle(overlay, 
                             (val_x_min - redact_margin, val_y_min - redact_margin), 
                             (val_x_max + redact_margin, val_y_max + redact_margin), 
                             (0, 0, 0), -1)
            else:
                # Blind redaction if value not detected but label exists
                blind_w = 400
                if scan_x_start + blind_w > img_w: blind_w = img_w - scan_x_start
                cv2.rectangle(overlay, 
                             (scan_x_start, label['y_min'] - redact_margin), 
                             (scan_x_start + blind_w, label['y_max'] + redact_margin), 
                             (0, 0, 0), -1)

        # Convert back to RGB and PIL
        result_image = cv2.cvtColor(overlay, cv2.COLOR_BGR2RGB)
        return Image.fromarray(result_image), extracted_data
        
    except Exception as e:
        logger.error(f"EasyOCR anonymization failed: {e}")
        return image, extracted_data


