from django.urls import path
from .views import BoardListCreateView, BoardDetailUpdateDeleteView

urlpatterns = [
    path('', BoardListCreateView.as_view(), name='boards-list-create'),
    path('<int:board_id>/', BoardDetailUpdateDeleteView.as_view(), name='boards-detail-update-delete'),
]
