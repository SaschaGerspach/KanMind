from django.urls import path

from .views import CommentCreateView, CommentListView, CommentDeleteView

urlpatterns = [
    path('<int:task_id>/comments/', CommentListView.as_view(), name='comment-list'),
    path('<int:task_id>/comments/', CommentCreateView.as_view(), name='comment-create'),
    path('<int:task_id>/comments/<int:comment_id>/', CommentDeleteView.as_view(), name='comment-delete'),
]
