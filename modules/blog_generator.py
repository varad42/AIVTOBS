from google import genai
import re

from config import GEMINI_API_KEY, GEMINI_MODEL

client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None


def _clean_blog_text(text):

    if not text:
        return ""

    cleaned_text = text.replace("**", "")
    cleaned_text = re.sub(r"\n{3,}", "\n\n", cleaned_text)

    return cleaned_text.strip()


def generate_blog(summary):

    prompt = f"""
    Write a clean blog article from this summary.

    Format it exactly like this:

    Title: ...

    Tags: ...

    Blog

    ...

    Conclusion

    ...

    Rules:
    Keep one blank line between each section.
    Do not use markdown headings.
    Do not use bullet points unless they are part of the actual blog content.
    Do not add extra labels or commentary.

    Summary:
    {summary}
    """

    try:
        if client is None:
            raise RuntimeError("GEMINI_API_KEY is not configured.")

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )

        text = response.text

        if not text:
            raise Exception("Empty response")

        return _clean_blog_text(text)

    except Exception as e:

        print("Gemini failed:", e)

        return _clean_blog_text(
            f"""
Title: Auto Generated Blog

Tags: AI, Summary

Blog

{summary}

Conclusion

This blog was generated using fallback mode because AI API failed.
""".strip()
        )
