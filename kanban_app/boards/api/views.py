from django.db.models import Count, Q, F, Value, IntegerField
from django.db.models.functions import Coalesce
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from ..models import Board
from .serializers import BoardListSerializer





class BoardListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BoardListSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Board.objects.filter(Q(owner=user) | Q(members=user)).distinct().select_related('owner')

        # Counts:
        # - member_count: Mitglieder (M2M) + Owner
        # - ticket_count: alle Tasks pro Board
        # - tasks_to_do_count: Tasks mit status='to_do'
        # - tasks_high_prio_count: Tasks mit priority='high'
    
        queryset = queryset.annotate(
            members_only=Count('members', distinct=True),
            ticket_count=Count('tasks', distinct=True),
            tasks_to_do_count=Count('tasks', filter=Q(tasks__status='to_do'), distinct=True),
            tasks_high_prio_count=Count('tasks', filter=Q(tasks__priority='high'), distinct=True),
        ).annotate(
            member_count=Coalesce(F('members_only'), Value(0)) + Value(1),  # +1 = Owner

        )

        return queryset
