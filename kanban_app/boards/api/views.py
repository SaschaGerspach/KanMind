from django.db.models import Q, Count, F, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from rest_framework.generics import ListCreateAPIView, RetrieveAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import PermissionDenied

from ..models import Board
from .serializers import BoardListSerializer, BoardCreateSerializer, BoardDetailSerializer, BoardUpdateResponseSerializer, BoardPatchSerializer

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
    


class BoardDetailUpdateView(RetrieveUpdateAPIView):
    """
    GET  /api/boards/{board_id}/   -> BoardDetailSerializer (wie zuvor)
    PATCH /api/boards/{board_id}/  -> BoardPatchSerializer (Input) + BoardUpdateResponseSerializer (Output)
    Zugriffsregel: Owner ODER Member, sonst 403.
    """
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = "board_id"

    def get_object(self):
        board_id = self.kwargs.get(self.lookup_url_kwarg)
        board = get_object_or_404(
            Board.objects.select_related("owner").prefetch_related("members", "tasks"),
            pk=board_id
        )
        user = self.request.user
        if not (board.owner_id == user.id or board.members.filter(pk=user.id).exists()):
            raise PermissionDenied("You do not have access to this board.")
        return board

    # GET -> wie gehabt
    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return BoardPatchSerializer
        return BoardDetailSerializer

    # PATCH -> Members ersetzen + optional Titel setzen, dann Response im PATCH-Format
    def patch(self, request, *args, **kwargs):
        board = self.get_object()

        in_serializer = BoardPatchSerializer(data=request.data, context={"request": request})
        in_serializer.is_valid(raise_exception=True)
        data = in_serializer.validated_data

        # Titel aktualisieren (wenn gesendet)
        if "title" in data:
            board.title = data["title"]
            board.save(update_fields=["title"])

        # Mitglieder ersetzen (wenn gesendet)
        if "members" in data:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            users = list(User.objects.filter(id__in=data["members"]))
            # kompletter Ersatz der M2M-Mitglieder
            board.members.set(users)

        out = BoardUpdateResponseSerializer(board)
        return Response(out.data, status=status.HTTP_200_OK)
