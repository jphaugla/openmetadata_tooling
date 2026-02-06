
import os
from google import genai

GEMINI_KEY = os.getenv("GEMINI_APIKEY")
client = genai.Client(api_key=GEMINI_KEY)

print("Listing models...")
try:
    for m in client.models.list_models():
        print(f"Model: {m.name}")
        if "generateContent" in m.supported_generation_methods:
             print(f"  - Supports generateContent: Yes")
except Exception as e:
    print(f"Error listing models: {e}")
