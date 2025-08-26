from django.urls import path

from .views import CommentListCreateView, CommentDeleteView

urlpatterns = [
    path('<int:task_id>/comments/', CommentListCreateView.as_view(), name='comment-list-create'),
    path('<int:task_id>/comments/<int:comment_id>/', CommentDeleteView.as_view(), name='comment-delete'),
]
