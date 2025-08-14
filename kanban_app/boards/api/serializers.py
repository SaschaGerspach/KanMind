from rest_framework import serializers
from ..models import Board, BoardMember
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from ...tasks.models import Task

User = get_user_model()

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
    


class UserLiteSerializer(serializers.ModelSerializer):
    fullname = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "email", "fullname"]

    def get_fullname(self, obj):
        # Falls first/last leer sind, nimm username als Fallback
        name = (obj.first_name or "") + (" " if obj.first_name and obj.last_name else "") + (obj.last_name or "")
        return name.strip() or obj.username


class TaskLiteSerializer(serializers.ModelSerializer):
    # Felder, die (noch) nicht im Model sind, liefern wir neutral
    description = serializers.SerializerMethodField()
    assignee   = serializers.SerializerMethodField()
    reviewer   = serializers.SerializerMethodField()
    due_date   = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            "id", "title",
            "description",
            "status", "priority",
            "assignee", "reviewer",
            "due_date",
            "comments_count",
        ]

    def get_description(self, obj):
        return getattr(obj, "description", None)

    def _user_or_none(self, u):
        return UserLiteSerializer(u).data if u else None

    def get_assignee(self, obj):
        return self._user_or_none(getattr(obj, "assignee", None))

    def get_reviewer(self, obj):
        return self._user_or_none(getattr(obj, "reviewer", None))

    def get_due_date(self, obj):
        # Erwartetes ISO-Format oder None
        due = getattr(obj, "due_date", None)
        return due if due is None else due.isoformat()

    def get_comments_count(self, obj):
        # 0, bis Comments-Relation existiert (z. B. obj.comments.count())
        return getattr(obj, "comments_count", 0)


class BoardDetailSerializer(serializers.ModelSerializer):
    owner_id = serializers.IntegerField(read_only=True)  # FK-Feld automatisch vorhanden
    members = serializers.SerializerMethodField()
    tasks   = serializers.SerializerMethodField()

    class Meta:
        model = Board
        fields = ["id", "title", "owner_id", "members", "tasks"]

    def get_members(self, obj):
        qs = obj.members.exclude(pk=obj.owner_id)
        return UserLiteSerializer(qs, many=True).data

    def get_tasks(self, obj):
        qs = obj.tasks.all().only("id", "title", "status", "priority")  # vorhandene Felder
        return TaskLiteSerializer(qs, many=True).data