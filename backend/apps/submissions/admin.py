from django.contrib import admin, messages
from django.utils.html import format_html

from . import services
from .models import VideoSubmission


@admin.register(VideoSubmission)
class VideoSubmissionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "student",
        "topic_display",
        "status_badge",
        "youtube_link",
        "created_at",
    )
    list_filter = ("status", "created_at", "topic__course")
    list_select_related = ("student", "topic", "topic__course", "reviewed_by")
    search_fields = (
        "student__username",
        "student__first_name",
        "topic__title",
        "topic__course__title",
        "telegram_file_id",
        "youtube_video_id",
    )
    readonly_fields = ("telegram_file_id", "created_at", "updated_at", "reviewed_at")
    raw_id_fields = ("student", "topic", "reviewed_by")
    actions = ["approve_submissions", "reject_submissions"]

    fieldsets = (
        (
            "Video ma'lumotlari",
            {
                "fields": (
                    "student",
                    "topic",
                    "status",
                    "telegram_file_id",
                    "youtube_video_id",
                )
            },
        ),
        (
            "Ko'rib chiqish",
            {
                "fields": (
                    "rejection_reason",
                    "reviewed_by",
                    "reviewed_at",
                )
            },
        ),
        (
            "Vaqt belgilari",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    @admin.display(description="Mavzu")
    def topic_display(self, obj):
        if not obj.topic:
            return format_html('<span style="color: #999;">— Tanlanmagan —</span>')
        return f"{obj.topic.course.title} → {obj.topic.title}"

    @admin.display(description="Holati")
    def status_badge(self, obj):
        colors = {
            VideoSubmission.STATUS_AWAITING_TOPIC: "#f59e0b",
            VideoSubmission.STATUS_PENDING_REVIEW: "#3b82f6",
            VideoSubmission.STATUS_APPROVED: "#10b981",
            VideoSubmission.STATUS_REJECTED: "#ef4444",
        }
        color = colors.get(obj.status, "#6b7280")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 9999px; font-weight: 500; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display(),
        )

    @admin.display(description="YouTube")
    def youtube_link(self, obj):
        if not obj.youtube_video_id:
            return "—"
        return format_html(
            '<a href="{}" target="_blank" rel="noopener noreferrer">Ko\'rish ({})</a>',
            obj.youtube_url,
            obj.youtube_video_id,
        )

    @admin.action(description="Tanlangan videolarni tasdiqlash (Approve)")
    def approve_submissions(self, request, queryset):
        count = 0
        for submission in queryset:
            services.approve_submission(submission, reviewer=request.user)
            count += 1
        self.message_user(
            request,
            f"{count} ta video muvaffaqiyatli tasdiqlandi va o'quvchilarga xabar yuborildi.",
            level=messages.SUCCESS,
        )

    @admin.action(description="Tanlangan videolarni rad etish (Reject)")
    def reject_submissions(self, request, queryset):
        count = 0
        for submission in queryset:
            services.reject_submission(
                submission,
                reviewer=request.user,
                reason="Darslik talablariga mos kelmadi.",
            )
            count += 1
        self.message_user(
            request,
            f"{count} ta video rad etildi va o'quvchilarga xabar yuborildi.",
            level=messages.WARNING,
        )
