import os
import traceback
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image, ImageDraw

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

# Create dummy image
img = Image.new('RGB', (100, 30), color=(73, 109, 137))
d = ImageDraw.Draw(img)
d.text((10, 10), "TEST", fill=(255, 255, 0))

try:
    print("Testing gemini-1.5-flash with image...")
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(["Describe this image", img])
    print("SUCCESS")
    print(response.text)
except Exception as e:
    print("FAILURE")
    print(e)
    # Write to a file so we can definitely see it
    with open("vision_error_log.txt", "w") as f:
        f.write(f"Error Type: {type(e)}\n")
        f.write(f"Error Message: {str(e)}\n")
        traceback.print_exc(file=f)
