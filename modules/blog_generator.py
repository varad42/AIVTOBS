from google import genai
from config import GEMINI_API_KEY


import os
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def generate_blog(summary):

    prompt = f"""
    Write a blog article from this summary.

    Include:
    Title
    Tags
    Blog Content

    Summary:
    {summary}
    """

    try:

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )

        text = response.text

        if not text:
            raise Exception("Empty response")

        return text

    except Exception as e:

        print("Gemini failed:", e)

        # ✅ fallback blog
        return f"""
Title: Auto Generated Blog

Tags: AI, Summary

Blog:

{summary}

Conclusion:
This blog was generated using fallback mode because AI API failed.
"""