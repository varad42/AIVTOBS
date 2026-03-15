import os

from google import genai


api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("Set GEMINI_API_KEY before running this script.")

client = genai.Client(api_key=api_key)

models = client.models.list()

for m in models:
    print(m.name)


