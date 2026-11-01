from django.db import models


class VideoSubmission(models.Model):
    """A student-submitted video lesson.

    Students send videos to the Telegram bot, which creates a submission
    in 'awaiting_topic' status. The student then binds the submission to a
    specific course Topic on the web platform, moving it to 'pending_review'.
    Administrators approve or reject the submission via the admin panel.
    Upon approval, the video is uploaded to YouTube and added to the course playlist.
    """

    STATUS_AWAITING_TOPIC = "awaiting_topic"
    STATUS_PENDING_REVIEW = "pending_review"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"

    STATUS_CHOICES = [
        (STATUS_AWAITING_TOPIC, "Mavzu biriktirilmagan"),
        (STATUS_PENDING_REVIEW, "Ko'rib chiqilmoqda"),
        (STATUS_APPROVED, "Tasdiqlangan"),
        (STATUS_REJECTED, "Rad etilgan"),
    ]

    student = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="video_submissions",
        verbose_name="O'quvchi",
    )
    topic = models.ForeignKey(
        "courses.Topic",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="video_submissions",
        verbose_name="Mavzu",
    )
    telegram_file_id = models.CharField(
        max_length=255,
        verbose_name="Telegram File ID",
    )
    status = models.CharField(
        max_length=32,
        choices=STATUS_CHOICES,
        default=STATUS_AWAITING_TOPIC,
        db_index=True,
        verbose_name="Holati",
    )
    youtube_video_id = models.CharField(
        max_length=64,
        blank=True,
        verbose_name="YouTube Video ID",
    )
    rejection_reason = models.TextField(
        blank=True,
        verbose_name="Rad etish sababi",
    )
    reviewed_by = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name="Ko'rib chiqqan admin",
    )
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Ko'rib chiqilgan vaqt",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name="Yaratilgan vaqt",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Tahrirlangan vaqt",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Video darslik"
        verbose_name_plural = "Video darsliklar"

    def __str__(self):
        topic_title = self.topic.title if self.topic else "Mavzusiz"
        return f"VideoSubmission #{self.pk} ({self.get_status_display()}) — {self.student.username} / {topic_title}"

    @property
    def youtube_url(self) -> str:
        if not self.youtube_video_id:
            return ""
        return f"https://www.youtube.com/watch?v={self.youtube_video_id}"

