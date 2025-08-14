from django.urls import path
from .views import BoardListCreateView

urlpatterns = [
    path('', BoardListCreateView.as_view(), name='boards-list-create'),
]
