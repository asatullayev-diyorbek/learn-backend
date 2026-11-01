from unittest.mock import MagicMock, patch

import pytest

from apps.accounts.models import User
from apps.courses.models import Category, Course, Instructor, Topic
from apps.submissions.models import VideoSubmission
from integrations.youtube.client import YouTubeClient
from integrations.youtube.uploader import process_submission_youtube_upload


@pytest.fixture
def sample_submission(db):
    user = User.objects.create(username="tg_user1", first_name="Diyorbek")
    category = Category.objects.create(name="Web", slug="web")
    instructor = Instructor.objects.create(full_name="Ustoz")
    course = Course.objects.create(
        title="React kursi",
        slug="react-kursi",
        summary="Qisqa",
        description="Batafsil",
        category=category,
        instructor=instructor,
    )
    topic = Topic.objects.create(course=course, title="Komponentlar", order=1)
    return VideoSubmission.objects.create(
        student=user,
        topic=topic,
        telegram_file_id="tg_file_id_react",
        status=VideoSubmission.STATUS_PENDING_REVIEW,
    )


def test_youtube_client_not_configured():
    with patch("integrations.youtube.client.get_access_token", return_value=None):
        client = YouTubeClient()
        assert client.is_configured() is False


@patch("integrations.youtube.uploader.YouTubeClient")
@patch("integrations.youtube.uploader.TelegramClient")
def test_process_submission_youtube_upload_success(
    mock_tg_class, mock_yt_class, sample_submission, settings, tmp_path
):
    settings.TELEGRAM_BOT_TOKEN = "123:test"

    # Mock telegram
    mock_tg = MagicMock()
    mock_tg_class.return_value = mock_tg
    mock_tg.get_file.return_value = {"result": {"file_path": "videos/test.mp4"}}

    def mock_download(path, dest):
        with open(dest, "wb") as f:
            f.write(b"video content")

    mock_tg.download_file.side_effect = mock_download

    # Mock youtube
    mock_yt = MagicMock()
    mock_yt_class.return_value = mock_yt
    mock_yt.is_configured.return_value = True
    mock_yt.find_or_create_playlist.return_value = "PL_test_123"
    mock_yt.upload_video.return_value = "yt_video_999"

    video_id = process_submission_youtube_upload(sample_submission)

    assert video_id == "yt_video_999"
    mock_yt.find_or_create_playlist.assert_called_once_with(
        title="React kursi",
        description="Learn platformasi: React kursi bo'yicha video darsliklar to'plami.",
    )
    mock_yt.upload_video.assert_called_once()
    mock_yt.add_video_to_playlist.assert_called_once_with("PL_test_123", "yt_video_999")
