"""Settings come from environment variables (.env locally; Key Vault / secrets in Azure)."""
import os

from dotenv import load_dotenv

load_dotenv()


class ConfigError(RuntimeError):
    """A required setting is missing. The message says what to fix."""


def get(name: str, required: bool = True, default: str = "") -> str:
    value = os.environ.get(name, "").strip() or default
    if required and not value:
        raise ConfigError(f"The setting {name} is missing. Add it to your .env file (see .env.example).")
    return value
