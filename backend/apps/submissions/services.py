import logging
from typing import Optional

from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import TelegramIdentity, User
from apps.accounts.services import get_or_create_user_for_telegram
from apps.courses.models import Course, Topic
from integrations.telegram.client import TelegramClient
from .models import VideoSubmission

logger = logging.getLogger(__name__)


def create_submission_from_telegram(
    telegram_id: int,
    file_id: str,
    username: Optional[str] = "",
    first_name: Optional[str] = "",
    last_name: Optional[str] = "",
) -> VideoSubmission:
    """Create a new submission from a video received by the Telegram bot."""
    user = get_or_create_user_for_telegram(
        telegram_id=telegram_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
    )
    return VideoSubmission.objects.create(
        student=user,
        telegram_file_id=file_id,
        status=VideoSubmission.STATUS_AWAITING_TOPIC,
    )


def get_user_submissions(user: User):
    """Return all submissions for the given user, ordered newest first."""
    return (
        VideoSubmission.objects.filter(student=user)
        .select_related("topic", "topic__course")
        .order_by("-created_at")
    )


def bind_submission_topic(submission: VideoSubmission, topic: Topic, user: User) -> VideoSubmission:
    """Bind a submission to a topic.

    Only the student who submitted the video can bind it, and only while
    it is in 'awaiting_topic' status.
    """
    if submission.student_id != user.id:
        raise PermissionDenied("Siz faqat o'zingizning videolaringizni biriktirishingiz mumkin.")

    if submission.status != VideoSubmission.STATUS_AWAITING_TOPIC:
        raise ValidationError("Faqat mavzu biriktirilmagan videolarni tahrirlash mumkin.")

    submission.topic = topic
    submission.status = VideoSubmission.STATUS_PENDING_REVIEW
    submission.save(update_fields=["topic", "status", "updated_at"])
    return submission


def approve_submission(
    submission: VideoSubmission,
    reviewer: Optional[User] = None,
    youtube_video_id: str = "",
) -> VideoSubmission:
    """Approve a video submission, updating status and reviewer audit info.

    Attempts to upload the video to YouTube if no youtube_video_id was supplied.
    """
    submission.status = VideoSubmission.STATUS_APPROVED
    submission.reviewed_by = reviewer
    submission.reviewed_at = timezone.now()

    if not youtube_video_id:
        try:
            from integrations.youtube.uploader import process_submission_youtube_upload
            uploaded_id = process_submission_youtube_upload(submission)
            if uploaded_id:
                youtube_video_id = uploaded_id
        except Exception as exc:
            logger.warning("YouTube upload failed for submission #%s: %s", submission.id, exc)

    if youtube_video_id:
        submission.youtube_video_id = youtube_video_id

    submission.save(
        update_fields=["status", "reviewed_by", "reviewed_at", "youtube_video_id", "updated_at"]
    )

    try:
        notify_student_about_approval(submission)
    except Exception as exc:
        logger.warning(
            "Failed to send approval notification for submission #%s: %s",
            submission.id,
            exc,
        )

    return submission


def reject_submission(
    submission: VideoSubmission,
    reviewer: Optional[User] = None,
    reason: str = "",
) -> VideoSubmission:
    """Reject a video submission with a reason."""
    submission.status = VideoSubmission.STATUS_REJECTED
    submission.reviewed_by = reviewer
    submission.reviewed_at = timezone.now()
    submission.rejection_reason = reason or "Belgilangan talablarga to'g'ri kelmadi."

    submission.save(
        update_fields=["status", "reviewed_by", "reviewed_at", "rejection_reason", "updated_at"]
    )

    try:
        notify_student_about_rejection(submission, submission.rejection_reason)
    except Exception as exc:
        logger.warning(
            "Failed to send rejection notification for submission #%s: %s",
            submission.id,
            exc,
        )

    return submission


def notify_student_about_approval(submission: VideoSubmission) -> None:
    """Send a Telegram notification to the student upon submission approval."""
    bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", "")
    if not bot_token:
        return

    identity = TelegramIdentity.objects.filter(user=submission.student).first()
    if not identity:
        return

    topic_title = submission.topic.title if submission.topic else "Mavzu"
    course_title = (
        submission.topic.course.title if submission.topic and submission.topic.course else "Kurs"
    )

    text = (
        f"🎉 <b>Tabriklaymiz!</b>\n\n"
        f"Siz yuborgan video darslik muvaffaqiyatli tasdiqlandi!\n\n"
        f"📚 <b>Kurs:</b> {course_title}\n"
        f"📖 <b>Mavzu:</b> {topic_title}\n"
    )

    if submission.youtube_url:
        text += f"▶️ <b>YouTube havola:</b> {submission.youtube_url}\n"

    text += (
        f"\nVideongiz tasdiqlandi va joylandi. Agar kanalga hamkor bo'lib qo'shilishni "
        f"xohlasangiz, administrator bilan bog'laning."
    )

    client = TelegramClient(bot_token=bot_token)
    client.send_message(chat_id=identity.telegram_id, text=text, parse_mode="HTML")


def notify_student_about_rejection(submission: VideoSubmission, reason: str) -> None:
    """Send a Telegram notification to the student upon submission rejection."""
    bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", "")
    if not bot_token:
        return

    identity = TelegramIdentity.objects.filter(user=submission.student).first()
    if not identity:
        return

    topic_title = submission.topic.title if submission.topic else "Mavzu"

    text = (
        f"⚠️ <b>Videodarslik ko'rib chiqildi</b>\n\n"
        f"Afsuski, sizning <b>'{topic_title}'</b> mavzusidagi videongiz qabul qilinmadi.\n\n"
        f"<b>Sababi:</b> {reason}\n\n"
        f"Iltimos, ko'rsatilgan kamchiliklarni to'g'rilab, qayta yuborishingiz mumkin."
    )

    client = TelegramClient(bot_token=bot_token)
    client.send_message(chat_id=identity.telegram_id, text=text, parse_mode="HTML")


def get_available_course_topics():
    """Return all published courses with their topics for student selection."""
    return (
        Course.objects.filter(is_published=True)
        .prefetch_related("topics")
        .order_by("title")
    )
