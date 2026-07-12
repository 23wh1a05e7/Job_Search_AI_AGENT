"""
Thin wrapper around the Anthropic Python SDK so the rest of the code
doesn't need to know API details.
"""

import anthropic
from src import config


def get_client() -> anthropic.Anthropic:
    if not config.ANTHROPIC_API_KEY:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set. Create a .env file (see .env.example) "
            "and set your API key before running the app."
        )
    return anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
