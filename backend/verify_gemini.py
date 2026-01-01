import os
import google.generativeai as genai

# Hardcoded API key
api_key = "AIzaSyBN8rqlRnhbEO6nlR2QCXYu5ZH7yqZtxQg"
print(f"API Key present: {bool(api_key)}")

try:
    genai.configure(api_key=api_key)
    # Using gemini-2.0-flash as listed in available models
    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content("Hello, this is a test. Reply with 'OK'.")
    print("Success! Response from Gemini:")
    print(response.text)
except Exception as e:
    print("Error calling Gemini:")
    print(e)
