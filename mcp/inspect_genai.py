
import os
from google import genai

GEMINI_KEY = os.getenv("GEMINI_APIKEY")
client = genai.Client(api_key=GEMINI_KEY)

print("Inspecting client.models...")
print(dir(client.models))

try:
    print("\nAttempting to generate content with gemini-2.0-flash-exp...")
    response = client.models.generate_content(
        model="gemini-2.0-flash-exp",
        contents="Hello"
    )
    print("Success with gemini-2.0-flash-exp")
except Exception as e:
    print(f"Failed with gemini-2.0-flash-exp: {e}")

try:
    print("\nAttempting to generate content with gemini-1.5-flash-latest...")
    response = client.models.generate_content(
        model="gemini-1.5-flash-latest",
        contents="Hello"
    )
    print("Success with gemini-1.5-flash-latest")
except Exception as e:
    print(f"Failed with gemini-1.5-flash-latest: {e}")
