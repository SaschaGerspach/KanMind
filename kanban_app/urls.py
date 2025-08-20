from django.urls import include, path

urlpatterns = [
    path("boards/", include("kanban_app.boards.api.urls")),
    path("tasks/", include("kanban_app.tasks.api.urls")),
    path("tasks/", include("kanban_app.comments.api.urls")),
]
