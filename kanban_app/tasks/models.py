
# kanban_app/tasks/models.py
from django.db import models

class Task(models.Model):
    PRIORITY = (('low','low'), ('medium','medium'), ('high','high'))
    STATUS = (('to_do','to_do'), ('in_progress','in_progress'), ('done','done'))

    board = models.ForeignKey('kanban_app.Board', related_name='tasks', on_delete=models.CASCADE)

    title = models.CharField(max_length=200)
    priority = models.CharField(max_length=10, choices=PRIORITY, default='medium')
    status = models.CharField(max_length=20, choices=STATUS, default='to_do')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
