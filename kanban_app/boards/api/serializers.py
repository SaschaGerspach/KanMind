from rest_framework import serializers
from ..models import Board, BoardMember
from django.contrib.auth import get_user_model
from django.db import IntegrityError

class BoardListSerializer(serializers.ModelSerializer):
    # owner_id kommt bei FK automatisch als <feld>_id -> nutzen wir direkt
    owner_id = serializers.IntegerField(read_only=True)

    # Zähler robust machen: wenn Annotation fehlt -> 0
    member_count = serializers.IntegerField(read_only=True, default=0, required=False)
    ticket_count = serializers.IntegerField(read_only=True, default=0, required=False)
    tasks_to_do_count = serializers.IntegerField(read_only=True, default=0, required=False)
    tasks_high_prio_count = serializers.IntegerField(read_only=True, default=0, required=False)

    class Meta:
        model = Board
        fields = [
            'id', 'title',
            'member_count', 'ticket_count',
            'tasks_to_do_count', 'tasks_high_prio_count',
            'owner_id'
        ]


class BoardCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200)
    members = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        allow_empty=True
    )

    def validate_members(self, value):
        # Deduplizieren & Existenz prüfen
        user_ids = list(dict.fromkeys(value))  # unique, Reihenfolge bleibt
        User = get_user_model()
        existing = set(User.objects.filter(id__in=user_ids).values_list('id', flat=True))
        missing = [uid for uid in user_ids if uid not in existing]
        if missing:
            raise serializers.ValidationError(f"Unknown user id(s): {missing}")
        return user_ids

    def create(self, validated_data):
        request = self.context['request']
        owner = request.user
        title = validated_data['title']
        member_ids = validated_data.get('members', [])

        board = Board.objects.create(title=title, owner=owner)

        # Mitglieder hinzufügen (Owner optional – nur, wenn mitgesendet)
        if member_ids:
            User = get_user_model()
            users = User.objects.filter(id__in=member_ids)
            # Konflikte (Owner doppelt etc.) ignorieren
            for u in users:
                try:
                    BoardMember.objects.create(board=board, user=u)
                except IntegrityError:
                    pass

        return board