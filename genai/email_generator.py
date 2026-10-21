"""Writes cart recovery emails with Gemini, falling back to a template.

Delivery must never depend on the AI: any failure (no key, timeout,
quota, bad output) returns the plain template instead.
"""

from google import genai
from google.genai import types
from pydantic import BaseModel

from backend.config.settings import (
    CURRENCY_SYMBOL,
    GEMINI_API_KEY,
    GEMINI_MODEL,
)
from genai.prompt_templates import (
    SYSTEM_PROMPT,
    build_user_prompt,
    fallback_email,
)

REQUEST_TIMEOUT_MS = 60_000
MAX_SUBJECT_LENGTH = 255


class RecoveryEmail(BaseModel):
    subject: str
    body: str


def generate_recovery_email(first_name, items, total):
    """Returns (subject, body, source), where source is "gemini" or "template"."""

    if GEMINI_API_KEY:
        try:
            email = _ask_gemini(first_name, items, total)
            return email.subject, email.body, "gemini"

        except Exception as exc:
            print(f"[GENAI ERROR] Using template email: {exc}")

    subject, body = fallback_email(
        first_name,
        items,
        total,
        CURRENCY_SYMBOL,
    )

    return subject, body, "template"


def _ask_gemini(first_name, items, total):
    client = genai.Client(
        api_key=GEMINI_API_KEY,
        http_options=types.HttpOptions(timeout=REQUEST_TIMEOUT_MS),
    )

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=build_user_prompt(
            first_name,
            items,
            total,
            CURRENCY_SYMBOL,
        ),
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=RecoveryEmail,
            temperature=0.7,
            # We give the model no tools, so skip the SDK's tool-calling loop.
            automatic_function_calling=types.AutomaticFunctionCallingConfig(
                disable=True,
            ),
        ),
    )

    email = response.parsed

    if (
        not isinstance(email, RecoveryEmail)
        or not email.subject.strip()
        or not email.body.strip()
    ):
        raise ValueError("Gemini returned an empty or malformed email")

    return RecoveryEmail(
        subject=email.subject.strip()[:MAX_SUBJECT_LENGTH],
        body=email.body.strip(),
    )
