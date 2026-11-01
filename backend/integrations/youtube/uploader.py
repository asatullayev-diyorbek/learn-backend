"""Uploader pipeline: Telegram -> YouTube -> Playlist."""

import logging
import os
import tempfile
from typing import Optional

from django.conf import settings

from integrations.telegram.client import TelegramClient
from .client import YouTubeClient

logger = logging.getLogger(__name__)


def process_submission_youtube_upload(submission) -> Optional[str]:
    """Download video from Telegram and upload to YouTube.

    If YouTube credentials are not configured or upload fails, logs the issue
    and returns None.
    """
    bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", "")
    if not bot_token:
        logger.warning("TELEGRAM_BOT_TOKEN not set; skipping YouTube upload.")
        return None

    youtube_client = YouTubeClient()
    if not youtube_client.is_configured():
        logger.info(
            "YouTube integration is not configured (missing OAuth credentials). "
            "Submission #%s marked approved without automatic upload.",
            submission.id,
        )
        return None

    telegram_client = TelegramClient(bot_token=bot_token)
    topic = submission.topic
    course = topic.course if topic else None
    course_title = course.title if course else "Learn Darsliklari"
    topic_title = topic.title if topic else f"Dars #{submission.id}"
    student_name = submission.student.get_full_name() or submission.student.username

    # Step 1: Get Telegram file info
    try:
        file_info = telegram_client.get_file(submission.telegram_file_id)
        file_path = file_info.get("result", {}).get("file_path")
        if not file_path:
            logger.error("Could not obtain file_path from Telegram for file %s", submission.telegram_file_id)
            return None
    except Exception as exc:
        logger.error("Failed to get file from Telegram: %s", exc)
        return None

    # Step 2: Download to a temp file
    temp_dir = tempfile.gettempdir()
    local_file_path = os.path.join(temp_dir, f"sub_{submission.id}_{os.path.basename(file_path)}")

    try:
        telegram_client.download_file(file_path, local_file_path)

        # Step 3: Find or create playlist
        playlist_id = youtube_client.find_or_create_playlist(
            title=course_title,
            description=f"Learn platformasi: {course_title} bo'yicha video darsliklar to'plami.",
        )

        # Step 4: Upload video
        privacy = getattr(settings, "YOUTUBE_DEFAULT_PRIVACY_STATUS", "unlisted")
        title = f"{course_title} — {topic_title}"
        description = (
            f"Kurs: {course_title}\n"
            f"Mavzu: {topic_title}\n"
            f"Muallif: {student_name}\n\n"
            f"Learn platformasi o'quvchilari tomonidan tayyorlangan darslik."
        )

        video_id = youtube_client.upload_video(
            file_path=local_file_path,
            title=title,
            description=description,
            privacy_status=privacy,
        )

        # Step 5: Add to playlist
        if playlist_id and video_id:
            try:
                youtube_client.add_video_to_playlist(playlist_id, video_id)
            except Exception as exc:
                logger.warning("Failed to add video %s to playlist %s: %s", video_id, playlist_id, exc)

        return video_id

    except Exception as exc:
        logger.error("YouTube upload pipeline failed for submission #%s: %s", submission.id, exc)
        return None

    finally:
        if os.path.exists(local_file_path):
            try:
                os.remove(local_file_path)
            except OSError:
                pass

