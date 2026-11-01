import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.types import Chat, Message, User as TgUser, Video

from apps.submissions.models import VideoSubmission
from bot.handlers.video import handle_video_submission


@pytest.mark.django_db
def test_handle_video_submission_success():
    # Setup mock message
    tg_user = TgUser(id=1234567, is_bot=False, first_name="Diyorbek", username="diyor")
    video = Video(
        file_id="video_file_unique_123",
        file_unique_id="unique_123",
        width=1920,
        height=1080,
        duration=60,
    )
    chat = Chat(id=1234567, type="private")

    message = MagicMock(spec=Message)
    message.from_user = tg_user
    message.video = video
    message.chat = chat
    message.answer = AsyncMock()
    message.send_copy = AsyncMock()

    with patch("django.conf.settings.TELEGRAM_REVIEW_CHANNEL_ID", "-100123456789"):
        asyncio.run(handle_video_submission(message))

    # Verify submission was created in database
    submission = VideoSubmission.objects.filter(student__username="tg_1234567").first()
    assert submission is not None
    assert submission.telegram_file_id == "video_file_unique_123"
    assert submission.status == VideoSubmission.STATUS_AWAITING_TOPIC
    assert submission.topic is None

    # Verify review channel copy was called
    message.send_copy.assert_awaited_once()
    assert message.send_copy.call_args[1]["chat_id"] == "-100123456789"

    # Verify user received answer
    message.answer.assert_awaited_once()
    assert "Videongiz qabul qilindi!" in message.answer.call_args[0][0]
