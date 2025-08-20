from django.urls import path

from .views import (
    AssignedToMeTaskListView,
    ReviewingTaskListView,
    TaskCreateView,
    TaskDetailUpdateDeleteView,
)

urlpatterns = [
    path("", TaskCreateView.as_view(), name="tasks-create"),
    path("assigned-to-me/", AssignedToMeTaskListView.as_view(), name="tasks-assigned-to-me"),
    path("reviewing/", ReviewingTaskListView.as_view(), name="tasks-reviewing"),
    path("<int:task_id>/", TaskDetailUpdateDeleteView.as_view(), name="task-detail-update-delete"),
]
