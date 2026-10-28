"""Pure helpers shared between the API views and the bot handlers.

Kept dependency-free (no Django, no aiogram) so both sides can import it
without pulling in the other's stack.
"""


def build_deep_link(bot_username: str, token: str) -> str:
    """Build a Telegram deep link that pre-fills /start <token>."""
    return f"https://t.me/{bot_username}?start={token}"
