from django.urls import path, include


urlpatterns = [
    path('boards/', include('kanban_app.boards.api.urls')),
    # path('columns/', include('kanban_app.columns.api.urls')),
    path('tasks/', include('kanban_app.tasks.api.urls')),
    # path('comments/', include('kanban_app.comments.api.urls')),
]