import os
import httpx
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openrouter/auto")  # let OpenRouter choose a free/available model

API_URL = "https://openrouter.ai/api/v1/chat/completions"

SYSTEM_PROMPT = (
    "You are a warm, trauma-informed mental health counselor. "
    "Be concise, kind, and practical. Never diagnose. "
    "Acknowledge feelings, reflect themes, and suggest one gentle action."
)

def _build_history_block(history_texts):
    """Turn recent entries into a compact block for context."""
    if not history_texts:
        return "No prior journal entries."
    lines = []
    for i, txt in enumerate(history_texts, start=1):
        lines.append(f"{i}. {txt}")
    return "Recent journal notes (oldest→newest):\n" + "\n".join(lines)

def generate_summary_affirmation(current_text: str, history_texts=None):
    """
    Ask the LLM for:
      - Summary: one empathetic line
      - Affirmation: one supportive line starting with 'Affirmation:'
    We include a short history to simulate 'memory'.
    """
    history_texts = history_texts or []

    user_prompt = (
        f"{_build_history_block(history_texts)}\n\n"
        f"Current entry:\n{current_text}\n\n"
        "Please respond in exactly two lines:\n"
        "Summary: <one warm, specific sentence>\n"
        "Affirmation: <one supportive sentence>"
    )

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    body = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        # Small max_tokens to keep costs tiny
        "max_tokens": 200,
        "temperature": 0.7,
    }

    try:
        with httpx.Client(timeout=30) as client:
            resp = client.post(API_URL, headers=headers, json=body)
            # Optional: debug prints
            print("LLM status:", resp.status_code)
            print("LLM resp:", resp.text[:800])
            resp.raise_for_status()
            data = resp.json()

        content = data["choices"][0]["message"]["content"].strip()

        # Robust parsing
        summary = None
        affirmation = None
        for line in content.splitlines():
            low = line.strip()
            if low.lower().startswith("summary:"):
                summary = line.split(":", 1)[1].strip()
            elif low.lower().startswith("affirmation:"):
                affirmation = line.split(":", 1)[1].strip()

        if not summary:
            summary = content.splitlines()[0].strip()
        if not affirmation:
            affirmation = "You're doing great. Keep going!"

        return summary, affirmation

    except httpx.HTTPStatusError as e:
        print("HTTP error:", e.response.text)
    except Exception as e:
        print("General LLM error:", str(e))

    # Fallbacks
    return "Could not generate summary.", "Could not generate affirmation."
