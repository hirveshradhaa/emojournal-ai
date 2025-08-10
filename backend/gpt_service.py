import os
import httpx
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")

def generate_summary_affirmation(text):
    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    body = {
        "model": "openai/gpt-3.5-turbo",  # ✅ Use a working model
        "messages": [
            {
                "role": "system",
                "content": "You are an empathetic assistant who helps users reflect on their emotions.",
            },
            {
                "role": "user",
                "content": f"Summarize this journal entry and give a kind affirmation:\n\n{text}",
            },
        ],
    }

    try:
        response = httpx.post(url, headers=headers, json=body, timeout=30)

        print(f"✅ Status Code: {response.status_code}")
        print("✅ Response Content:", response.text)

        response.raise_for_status()
        result = response.json()

        content = result["choices"][0]["message"]["content"]

        if "\n" in content:
            summary, affirmation = content.strip().split("\n", 1)
        else:
            summary = content.strip()
            affirmation = "You're doing great. Keep going!"

        return summary.strip(), affirmation.strip()

    except httpx.HTTPStatusError as e:
        print("❌ HTTP Error Response:", e.response.text)
        return "Could not generate summary.", "Could not generate affirmation."

    except Exception as e:
        print("❌ General Exception:", str(e))
        return "Could not generate summary.", "Could not generate affirmation."
