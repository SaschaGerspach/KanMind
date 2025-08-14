from django.urls import path
from .views import BoardListCreateView, BoardDetailUpdateView

urlpatterns = [
    path('', BoardListCreateView.as_view(), name='boards-list-create'),
    path('<int:board_id>/', BoardDetailUpdateView.as_view(), name='boards-detail-update'),
]
