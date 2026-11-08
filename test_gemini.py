import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

try:
    response = client.interactions.create(
        model="gemini-4-argon",
        input="Explain nitrogen, phosphorus and potassium in crop growth."
    )

    print("GEMINI WORKING!")
    print(response.output_text)

except Exception as e:
    print("GEMINI TEST FAILED")
    print(type(e).__name__)
    print(str(e))