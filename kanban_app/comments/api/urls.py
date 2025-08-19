from django.urls import path
from .views import CommentCreateView

urlpatterns = [
    path('<int:task_id>/comments/', CommentCreateView.as_view(), name='task-add-comment'),
]
