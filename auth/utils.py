import re


EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def normalize_email(value):

    return (value or "").strip().lower()


def is_valid_email(value):

    return bool(EMAIL_REGEX.match(normalize_email(value)))


def validate_password(password):

    password = password or ""

    if len(password) < 8:
        return "Password must be at least 8 characters long."

    return None
