import os
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image, ImageDraw

# Load env
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

# Create dummy image
img = Image.new('RGB', (100, 30), color=(73, 109, 137))
d = ImageDraw.Draw(img)
d.text((10, 10), "Hello World", fill=(255, 255, 0))

print("Created dummy image.")

try:
    print("Attempting to call gemini-2.0-flash with image...")
    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content(["Tell me what is in this image", img])
    print("Success!")
    print(response.text)
except Exception as e:
    print("FAILURE:")
    print(e)
