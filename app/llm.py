"""Azure OpenAI access: embeddings and chat completions."""
from functools import lru_cache

from openai import AzureOpenAI

from app import config


class LLMError(RuntimeError):
    """Azure OpenAI could not complete the request (message is safe to show)."""


@lru_cache(maxsize=1)
def _client() -> AzureOpenAI:
    return AzureOpenAI(
        azure_endpoint=config.get("AZURE_OPENAI_ENDPOINT"),
        api_key=config.get("AZURE_OPENAI_KEY"),
        api_version="2024-10-21",
    )


def _friendly(exc: Exception) -> LLMError:
    name = type(exc).__name__
    if "Authentication" in name or "PermissionDenied" in name:
        return LLMError("Azure OpenAI rejected the request: the key or endpoint is missing or incorrect.")
    if "NotFound" in name:
        return LLMError("Azure OpenAI could not find the model deployment. Check the deployment names in .env.")
    if "RateLimit" in name:
        return LLMError("Azure OpenAI is receiving too many requests. Wait a minute and try again.")
    return LLMError(f"Azure OpenAI is unavailable right now ({name}).")


def embed(text: str) -> list[float]:
    try:
        r = _client().embeddings.create(model=config.get("AZURE_OPENAI_EMBEDDING_DEPLOYMENT"), input=text)
    except config.ConfigError:
        raise
    except Exception as exc:
        raise _friendly(exc) from exc
    return r.data[0].embedding


def chat(messages: list[dict], temperature: float = 0.1, json_mode: bool = False) -> dict:
    """Return {"text": str, "tokens": int}. json_mode forces a valid JSON object reply."""
    extra = {"response_format": {"type": "json_object"}} if json_mode else {}
    try:
        r = _client().chat.completions.create(
            model=config.get("AZURE_OPENAI_CHAT_DEPLOYMENT"), messages=messages, temperature=temperature, **extra
        )
    except config.ConfigError:
        raise
    except Exception as exc:
        raise _friendly(exc) from exc
    return {"text": r.choices[0].message.content or "", "tokens": r.usage.total_tokens}
