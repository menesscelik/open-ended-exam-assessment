import os
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image, ImageDraw

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

img = Image.new('RGB', (100, 30), color=(73, 109, 137))
d = ImageDraw.Draw(img)
d.text((10, 10), "Test", fill=(255, 255, 0))

models_to_try = ['gemini-1.5-flash', 'gemini-1.5-flash-latest', 'gemini-1.5-pro', 'gemini-pro-vision']

for model_name in models_to_try:
    print(f"Testing model: {model_name}")
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(["Test", img])
        print(f"SUCCESS with {model_name}")
        break 
    except Exception as e:
        print(f"FAILED {model_name}: {e}")
