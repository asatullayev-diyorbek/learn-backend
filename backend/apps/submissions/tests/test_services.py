import pytest
from unittest.mock import patch

from django.core.exceptions import PermissionDenied, ValidationError

from apps.accounts.models import TelegramIdentity, User
from apps.courses.models import Category, Course, Instructor, Topic
from apps.submissions.models import VideoSubmission
from apps.submissions import services


@pytest.fixture
def test_setup():
    category = Category.objects.create(name="Backend", slug="backend")
    instructor = Instructor.objects.create(full_name="Ustoz")
    course = Course.objects.create(
        title="Django kursi",
        slug="django-kursi",
        summary="Qisqa",
        description="Batafsil",
        category=category,
        instructor=instructor,
    )
    topic = Topic.objects.create(course=course, title="1-dars: Kirish", order=1)
    return {"course": course, "topic": topic}


@pytest.mark.django_db
def test_create_submission_from_telegram():
    submission = services.create_submission_from_telegram(
        telegram_id=999888777,
        file_id="video_file_id_xyz",
        username="alisher",
        first_name="Alisher",
    )

    assert submission.pk is not None
    assert submission.student.username == "tg_999888777"
    assert submission.telegram_file_id == "video_file_id_xyz"
    assert submission.status == VideoSubmission.STATUS_AWAITING_TOPIC
    assert submission.topic is None


@pytest.mark.django_db
def test_bind_submission_topic_success(test_setup):
    topic = test_setup["topic"]
    user = User.objects.create(username="tg_111")
    submission = VideoSubmission.objects.create(
        student=user,
        telegram_file_id="tg_file_1",
        status=VideoSubmission.STATUS_AWAITING_TOPIC,
    )

    updated = services.bind_submission_topic(submission, topic, user)
    assert updated.topic == topic
    assert updated.status == VideoSubmission.STATUS_PENDING_REVIEW


@pytest.mark.django_db
def test_bind_submission_topic_permission_denied(test_setup):
    topic = test_setup["topic"]
    owner = User.objects.create(username="tg_owner")
    other_user = User.objects.create(username="tg_other")
    submission = VideoSubmission.objects.create(
        student=owner,
        telegram_file_id="tg_file_1",
        status=VideoSubmission.STATUS_AWAITING_TOPIC,
    )

    with pytest.raises(PermissionDenied):
        services.bind_submission_topic(submission, topic, other_user)


@pytest.mark.django_db
def test_bind_submission_topic_invalid_status(test_setup):
    topic = test_setup["topic"]
    user = User.objects.create(username="tg_111")
    submission = VideoSubmission.objects.create(
        student=user,
        telegram_file_id="tg_file_1",
        status=VideoSubmission.STATUS_PENDING_REVIEW,
    )

    with pytest.raises(ValidationError):
        services.bind_submission_topic(submission, topic, user)


@pytest.mark.django_db
@patch("apps.submissions.services.TelegramClient.send_message")
def test_approve_submission_triggers_notification(mock_send, test_setup):
    topic = test_setup["topic"]
    user = User.objects.create(username="tg_student")
    TelegramIdentity.objects.create(user=user, telegram_id=555444)
    admin_user = User.objects.create(username="admin_user", is_staff=True)

    submission = VideoSubmission.objects.create(
        student=user,
        topic=topic,
        telegram_file_id="tg_file_1",
        status=VideoSubmission.STATUS_PENDING_REVIEW,
    )

    with patch("django.conf.settings.TELEGRAM_BOT_TOKEN", "123:fake_token"):
        services.approve_submission(
            submission,
            reviewer=admin_user,
            youtube_video_id="video123",
        )

    submission.refresh_from_db()
    assert submission.status == VideoSubmission.STATUS_APPROVED
    assert submission.reviewed_by == admin_user
    assert submission.youtube_video_id == "video123"
    assert mock_send.called
    assert "https://www.youtube.com/watch?v=video123" in mock_send.call_args[1]["text"]


@pytest.mark.django_db
@patch("apps.submissions.services.TelegramClient.send_message")
def test_reject_submission_triggers_notification(mock_send, test_setup):
    topic = test_setup["topic"]
    user = User.objects.create(username="tg_student")
    TelegramIdentity.objects.create(user=user, telegram_id=555444)
    admin_user = User.objects.create(username="admin_user", is_staff=True)

    submission = VideoSubmission.objects.create(
        student=user,
        topic=topic,
        telegram_file_id="tg_file_1",
        status=VideoSubmission.STATUS_PENDING_REVIEW,
    )

    with patch("django.conf.settings.TELEGRAM_BOT_TOKEN", "123:fake_token"):
        services.reject_submission(
            submission,
            reviewer=admin_user,
            reason="Ovoz sifati past.",
        )

    submission.refresh_from_db()
    assert submission.status == VideoSubmission.STATUS_REJECTED
    assert submission.rejection_reason == "Ovoz sifati past."
    assert mock_send.called
    assert "Ovoz sifati past." in mock_send.call_args[1]["text"]
