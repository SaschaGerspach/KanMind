from rest_framework import serializers
from ..models import Board

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
