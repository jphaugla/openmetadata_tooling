
import os
from google import genai

GEMINI_KEY = os.getenv("GEMINI_APIKEY")
client = genai.Client(api_key=GEMINI_KEY)

print("Listing models with client.models.list()...")
try:
    for m in client.models.list():
        print(f"Model: {m.name}")
except Exception as e:
    print(f"Error listing models: {e}")
