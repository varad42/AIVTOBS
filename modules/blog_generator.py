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

    Include:
    Title
    Tags
    Blog Content

    Formatting rules:
    Use Markdown headings.
    Put each section on its own line with a blank line between sections.
    Use this structure:
    # Title

    **Tags:** ...

    ## Blog

    ...

    ## Conclusion

    ...

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

        # ✅ fallback blog
        return _clean_blog_text(
            f"""
# Auto Generated Blog

**Tags:** AI, Summary

## Blog

{summary}

## Conclusion

This blog was generated using fallback mode because AI API failed.
""".strip()
        )
