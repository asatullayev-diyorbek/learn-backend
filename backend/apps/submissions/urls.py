from django.urls import path

from . import views

app_name = "submissions"

urlpatterns = [
    path("mine/", views.MySubmissionsView.as_view(), name="my-submissions"),
    path("<int:pk>/bind/", views.BindTopicView.as_view(), name="bind-topic"),
    path("available-topics/", views.AvailableTopicsView.as_view(), name="available-topics"),
]

