from google import genai
from config import GEMINI_API_KEY

client = genai.Client(api_key=GEMINI_API_KEY)


def generate_blog(summary_text):

    prompt = f"""
Convert the following summary into a proper blog article.

Requirements:
- Add title
- Add introduction
- Add headings
- Add conclusion
- Make it readable like blog

Summary:
{summary_text}
"""

    response = client.models.generate_content(
        model="gemini-flash-latest",
        contents=prompt
    )

    return response.text