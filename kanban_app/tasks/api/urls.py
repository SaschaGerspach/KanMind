from django.urls import path
from .views import TaskCreateView, AssignedToMeTaskListView
urlpatterns = [
    # Alle Tasks eines Boards erstellen/auflisten
    path('', TaskCreateView.as_view(), name='tasks-create'),
    path('assigned-to-me/', AssignedToMeTaskListView.as_view(), name='tasks-assigned-to-me'),
]