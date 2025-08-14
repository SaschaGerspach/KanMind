from django.urls import path
from .views import BoardListCreateView, BoardDetailView

urlpatterns = [
    path('', BoardListCreateView.as_view(), name='boards-list-create'),
    path('<int:board_id>/', BoardDetailView.as_view(), name='boards-detail'),
]
