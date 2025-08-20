from django.db.models import Q, Count, F, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import Board
from .serializers import (
    BoardCreateSerializer,
    BoardDetailSerializer,
    BoardListSerializer,
    BoardPatchSerializer,
    BoardUpdateResponseSerializer,
)


class BoardListCreateView(ListCreateAPIView):
    """
    API endpoint for listing all boards the user has access to
    or creating a new board.
    """

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        # Use a different serializer depending on request type
        return BoardCreateSerializer if self.request.method == "POST" else BoardListSerializer

    def get_queryset(self):
        """
        Return boards where the user is either the owner or a member.
        Adds annotation fields like task counts and member counts.
        """
        user = self.request.user
        queryset = (
            Board.objects.filter(Q(owner=user) | Q(members=user))
            .distinct()
            .select_related("owner")
        )

        queryset = queryset.annotate(
            members_only=Count("members", distinct=True),
            ticket_count=Count("tasks", distinct=True),
            tasks_to_do_count=Count("tasks", filter=Q(tasks__status="to_do"), distinct=True),
            tasks_high_prio_count=Count("tasks", filter=Q(tasks__priority="high"), distinct=True),
        ).annotate(
            member_count=Coalesce(F("members_only"), Value(0))
        )
        return queryset

    def create(self, request, *args, **kwargs):
        """
        Create a new board with the given data and return it
        with annotation fields for members and tasks.
        """
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        board = serializer.save()

        annotated = (
            Board.objects.filter(pk=board.pk)
            .select_related("owner")
            .annotate(
                members_only=Count("members", distinct=True),
                ticket_count=Count("tasks", distinct=True),
                tasks_to_do_count=Count("tasks", filter=Q(tasks__status="to_do"), distinct=True),
                tasks_high_prio_count=Count("tasks", filter=Q(tasks__priority="high"), distinct=True),
            )
            .annotate(member_count=Coalesce(F("members_only"), Value(0)))
            .first()
        )
        out = BoardListSerializer(annotated)
        return Response(out.data, status=status.HTTP_201_CREATED)


class BoardDetailUpdateDeleteView(RetrieveUpdateDestroyAPIView):
    """
    API endpoint for retrieving, updating or deleting a single board.
    Access is restricted to board owners and members.
    """

    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = "board_id"

    def get_object(self):
        """
        Fetch the board by ID, making sure the requesting user
        is allowed to access it.
        """
        board_id = self.kwargs.get(self.lookup_url_kwarg)
        board = get_object_or_404(
            Board.objects.select_related("owner").prefetch_related("members", "tasks"),
            pk=board_id,
        )
        user = self.request.user

        # Only the owner can delete the board
        if self.request.method == "DELETE":
            if board.owner_id != user.id:
                raise PermissionDenied("Only the owner can delete this board.")
            return board

        # For other requests: allow owner and members
        if not (board.owner_id == user.id or board.members.filter(pk=user.id).exists()):
            raise PermissionDenied("You do not have access to this board.")
        return board

    def get_serializer_class(self):
        # Use patch serializer for partial updates, detail otherwise
        if self.request.method == "PATCH":
            return BoardPatchSerializer
        return BoardDetailSerializer

    def patch(self, request, *args, **kwargs):
        """
        Update board fields (title and/or members).
        Returns a custom response serializer with owner and members info.
        """
        board = self.get_object()
        in_serializer = BoardPatchSerializer(data=request.data, context={"request": request})
        in_serializer.is_valid(raise_exception=True)
        data = in_serializer.validated_data

        # Update title if provided
        if "title" in data:
            board.title = data["title"]
            board.save(update_fields=["title"])

        # Update members if provided
        if "members" in data:
            from django.contrib.auth import get_user_model

            User = get_user_model()
            users = list(User.objects.filter(id__in=data["members"]))
            board.members.set(users)

        out = BoardUpdateResponseSerializer(board)
        return Response(out.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        """
        Delete the board if the requesting user is the owner.
        """
        board = self.get_object()
        if board.owner_id != request.user.id:
            raise PermissionDenied("Only the owner can delete this board.")
        board.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
