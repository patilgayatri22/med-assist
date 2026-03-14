import os
import json
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv
from openai import OpenAI

# Load .env from backend dir, then frontend .env.local
_backend_dir = Path(__file__).resolve().parent
load_dotenv(_backend_dir / ".env")
load_dotenv(_backend_dir / ".." / "frontend" / ".env.local")

# Accept FEATHERLESS_API_KEY, OPENAI_API_KEY, or VITE_OPENAI_API_KEY
FEATHERLESS_API_KEY = (
    os.getenv("FEATHERLESS_API_KEY")
    or os.getenv("OPENAI_API_KEY")
    or os.getenv("VITE_OPENAI_API_KEY")
)
MODEL_NAME = os.getenv("MODEL_NAME", "meta-llama/Llama-3.1-8B-Instruct")

if not FEATHERLESS_API_KEY:
    raise ValueError(
        "API key is missing. Set FEATHERLESS_API_KEY, OPENAI_API_KEY, or VITE_OPENAI_API_KEY "
        "in backend/.env or frontend/.env.local"
    )

client = OpenAI(
    base_url="https://api.featherless.ai/v1",
    api_key=FEATHERLESS_API_KEY,
)

def ask_llama(user_prompt: str, system_prompt: str, temperature: float = 0.2) -> str:
    """
    Sends a chat completion request to Featherless using the OpenAI SDK format.
    Returns plain text response content.
    """
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
    )

    return response.choices[0].message.content.strip()


def ask_llama_json(user_prompt: str, system_prompt: str, temperature: float = 0.1) -> Dict[str, Any]:
    """
    Requests JSON output from the model and parses it safely.
    """
    raw_text = ask_llama(
        user_prompt=user_prompt,
        system_prompt=system_prompt,
        temperature=temperature,
    )

    # Clean up markdown formatting
    cleaned_text = raw_text.strip()

    # Remove markdown code blocks if present
    if cleaned_text.startswith("```json"):
        cleaned_text = cleaned_text[7:]  # Remove ```json
    if cleaned_text.startswith("```"):
        cleaned_text = cleaned_text[3:]   # Remove ```
    if cleaned_text.endswith("```"):
        cleaned_text = cleaned_text[:-3]  # Remove trailing ```

    cleaned_text = cleaned_text.strip()

    try:
        return json.loads(cleaned_text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "Model did not return valid JSON.\n"
            f"Raw response:\n{raw_text}\n"
            f"Cleaned text:\n{cleaned_text}"
        ) from exc