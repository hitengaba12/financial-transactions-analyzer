import logging
import time
from typing import Dict, Iterable, List

import requests

from app.utils.settings import settings

logger = logging.getLogger(__name__)

CATEGORIES = [
    "Food",
    "Shopping",
    "Travel",
    "Transport",
    "Utilities",
    "Cash Withdrawal",
    "Entertainment",
    "Other",
]

MAX_BATCH_SIZE = 10
RETRY_COUNT = 3
RETRY_BACKOFF_SECONDS = 5


def build_prompt(merchants: List[str]) -> str:
    merchant_lines = "\n".join(f"- {merchant}" for merchant in merchants)
    return (
        "You are a transaction classification assistant. "
        "Classify each merchant into one of these categories: Food, Shopping, Travel, Transport, Utilities, Cash Withdrawal, Entertainment, Other. "
        "Respond with one merchant per line in the format Merchant: Category. "
        "If the merchant is ambiguous, choose the most likely category from the list.\n\n"
        f"Merchants:\n{merchant_lines}\n"
    )


def parse_response(text: str, merchants: List[str]) -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in lines:
        if ":" not in line:
            continue
        merchant_value, category_value = line.split(":", 1)
        merchant_key = merchant_value.strip()
        category = category_value.strip().title()
        if category not in CATEGORIES:
            category = "Other"
        matching = [m for m in merchants if m.lower() == merchant_key.lower()]
        if matching:
            mapping[matching[0]] = category
        else:
            for candidate in merchants:
                if merchant_key.lower() in candidate.lower() or candidate.lower() in merchant_key.lower():
                    mapping[candidate] = category
    for merchant in merchants:
        mapping.setdefault(merchant, "Other")
    return mapping


def call_gemini(prompt: str) -> str | None:
    if not settings.gemini_api_key:
        logger.warning("Gemini API key not configured, skipping external classification.")
        return None

    url = f"https://api.generativeai.googleapis.com/v1beta2/models/{settings.gemini_model}:generateText"
    headers = {
        "Authorization": f"Bearer {settings.gemini_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "prompt": {
            "messages": [
                {"role": "user", "content": prompt},
            ]
        },
        "temperature": 0.2,
        "maxOutputTokens": 256,
    }
    response = requests.post(url, json=payload, headers=headers, timeout=30)
    response.raise_for_status()
    body = response.json()
    if "candidates" in body and body["candidates"]:
        return body["candidates"][0].get("content", "")
    if "output" in body and "content" in body["output"]:
        return body["output"]["content"]
    return None


def merchant_category_map(merchant_names: Iterable[str]) -> Dict[str, str]:
    merchants = [name.strip() for name in merchant_names if name and name.strip()]
    if not merchants:
        return {}

    categories: Dict[str, str] = {}
    for idx in range(0, len(merchants), MAX_BATCH_SIZE):
        batch = merchants[idx : idx + MAX_BATCH_SIZE]
        prompt = build_prompt(batch)
        attempt = 0
        while attempt < RETRY_COUNT:
            attempt += 1
            try:
                response = call_gemini(prompt)
                if not response:
                    raise RuntimeError("Gemini response empty or unavailable")
                batch_map = parse_response(response, batch)
                categories.update(batch_map)
                break
            except Exception as exc:
                logger.warning(
                    "Gemini classification attempt %s failed for batch %s: %s",
                    attempt,
                    batch,
                    exc,
                )
                if attempt >= RETRY_COUNT:
                    for merchant in batch:
                        categories[merchant] = "Other"
                else:
                    time.sleep(RETRY_BACKOFF_SECONDS * attempt)
    return categories
