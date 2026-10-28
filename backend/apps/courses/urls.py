from django.urls import path

from . import views

app_name = "courses"

urlpatterns = [
    path("", views.CourseListView.as_view(), name="course-list"),
    # Must stay above the <slug> route so "categories" isn't read as a course slug.
    path("categories/", views.CategoryListView.as_view(), name="category-list"),
    path("<slug:slug>/", views.CourseDetailView.as_view(), name="course-detail"),
    path("<slug:slug>/enroll/", views.CourseEnrollView.as_view(), name="course-enroll"),
]
