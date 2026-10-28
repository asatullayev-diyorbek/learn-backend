"""Thin async wrappers around apps.accounts.services for aiogram handlers.

aiogram handlers run on an asyncio event loop; Django's ORM calls are
synchronous, so every call into apps.accounts.services is wrapped with
sync_to_async(thread_sensitive=True) here (thread_sensitive keeps all ORM
access on Django's single "sync" thread, avoiding cross-thread connection
issues with sqlite/postgres).
"""

from asgiref.sync import sync_to_async

from apps.accounts import services as _services

confirm_auth_challenge = sync_to_async(_services.confirm_auth_challenge, thread_sensitive=True)
create_login_code = sync_to_async(_services.create_login_code, thread_sensitive=True)
