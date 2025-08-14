from django.db.models import Q, Count, F, Value
from django.db.models.functions import Coalesce
from rest_framework.generics import ListCreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from ..models import Board
from .serializers import BoardListSerializer, BoardCreateSerializer

class BoardListCreateView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        # GET -> Liste; POST -> Create
        return BoardCreateSerializer if self.request.method == 'POST' else BoardListSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = (
            Board.objects
            .filter(Q(owner=user) | Q(members=user))
            .distinct()
            .select_related('owner')
        )

        # Zähler wie bei GET
        queryset = queryset.annotate(
            members_only=Count('members', distinct=True),
            ticket_count=Count('tasks', distinct=True),
            tasks_to_do_count=Count('tasks', filter=Q(tasks__status='to_do'), distinct=True),
            tasks_high_prio_count=Count('tasks', filter=Q(tasks__priority='high'), distinct=True),
        ).annotate(
            member_count=Coalesce(F('members_only'), Value(0))
        )
        return queryset

    def create(self, request, *args, **kwargs):
        # Validieren & anlegen
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        board = serializer.save()

        # Antwort exakt wie bei GET-Format (mit Counts etc.)
        annotated = (
            Board.objects
            .filter(pk=board.pk)
            .select_related('owner')
            .annotate(
                members_only=Count('members', distinct=True),
                ticket_count=Count('tasks', distinct=True),
                tasks_to_do_count=Count('tasks', filter=Q(tasks__status='to_do'), distinct=True),
                tasks_high_prio_count=Count('tasks', filter=Q(tasks__priority='high'), distinct=True),
            ).annotate(
                member_count=Coalesce(F('members_only'), Value(0))
            )
            .first()
        )
        out = BoardListSerializer(annotated)
        return Response(out.data, status=status.HTTP_201_CREATED)
