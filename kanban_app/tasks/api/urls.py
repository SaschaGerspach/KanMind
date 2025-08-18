from django.urls import path
from .views import TaskCreateView
urlpatterns = [
    # Alle Tasks eines Boards erstellen/auflisten
    path('', TaskCreateView.as_view(), name='tasks-create')

]