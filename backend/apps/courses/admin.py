from django.contrib import admin
from django.db.models import Count

from .models import Category, Course, Enrollment, Instructor


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Instructor)
class InstructorAdmin(admin.ModelAdmin):
    list_display = ("full_name", "title")
    search_fields = ("full_name", "title")


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "category",
        "instructor",
        "level",
        "is_published",
        "enrolled_count",
        "created_at",
    )
    list_filter = ("is_published", "level", "category")
    list_editable = ("is_published",)
    list_select_related = ("category", "instructor")
    search_fields = ("title", "slug", "summary")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("created_at", "updated_at")

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_enrolled_count=Count("enrollments"))

    @admin.display(description="Enrolled", ordering="_enrolled_count")
    def enrolled_count(self, obj):
        return obj._enrolled_count


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "course", "enrolled_at")
    list_filter = ("course__category", "course")
    list_select_related = ("user", "course")
    search_fields = ("user__username", "user__first_name", "course__title", "course__slug")
    raw_id_fields = ("user", "course")
    readonly_fields = ("enrolled_at",)
