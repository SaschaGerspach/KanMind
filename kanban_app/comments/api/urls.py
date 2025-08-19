from django.urls import path
from .views import CommentCreateView, CommentListView

urlpatterns = [
    path('<int:task_id>/comments/', CommentListView.as_view(), name='comment-list'),
    path('<int:task_id>/comments/', CommentCreateView.as_view(), name='comment-create'),
]
