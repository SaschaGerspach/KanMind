from django.urls import path
from .views import TaskCreateView, AssignedToMeTaskListView, ReviewingTaskListView, TaskUpdateView
urlpatterns = [
    # Alle Tasks eines Boards erstellen/auflisten
    path('', TaskCreateView.as_view(), name='tasks-create'),
    path('assigned-to-me/', AssignedToMeTaskListView.as_view(), name='tasks-assigned-to-me'),
    path('reviewing/', ReviewingTaskListView.as_view(), name='tasks-reviewing'),
    path('<int:task_id>/', TaskUpdateView.as_view(), name='tasks-update'),

]