"""Sends a prompt to Gemini. Retries are bounded, and the client can be swapped in tests."""
import os
import time

from dotenv import load_dotenv
from openai import APIConnectionError, APITimeoutError, OpenAI, RateLimitError

load_dotenv()

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
RETRYABLE = (RateLimitError, APITimeoutError, APIConnectionError)


def get_client() -> OpenAI:
    return OpenAI(
        api_key=os.getenv("GEMINI_API_KEY"),
        base_url=GEMINI_URL,
        timeout=float(os.getenv("LLM_TIMEOUT_SECONDS", "30")),
    )


def get_model() -> str:
    return os.getenv("LLM_MODEL", "gemini-2.5-flash")


def build_messages(system_prompt: str, user_text: str) -> list[dict]:
    """Pack the rules (system) and the question (user) into the list Gemini expects."""
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_text},
    ]


def ask_llm(system_prompt, user_message, client=None, max_retries=3, sleep=time.sleep) -> str:
    """Return the model's text reply. Retries on rate limits, timeouts, and
    connection errors, waiting longer each time. Gives up after max_retries."""
    client = client or get_client()
    for attempt in range(1, max_retries + 1):
        try:
            response = client.chat.completions.create(
                model=get_model(),
                messages=build_messages(system_prompt, user_message)
            )
            return response.choices[0].message.content
        except RETRYABLE:
            if attempt == max_retries:
                raise  # out of tries: let the caller handle it
            sleep(20 * attempt)  # waits 20s, then 40s