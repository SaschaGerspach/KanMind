from django.db import models
from django.contrib.auth import get_user_model
from ..boards.models import Board

User = get_user_model()


class Task(models.Model):
    PRIORITY = (('low', 'low'), ('medium', 'medium'), ('high', 'high'))
    STATUS = (('to-do', 'to-do'), ('in-progress', 'in-progress'),
              ('review', 'review'), ('done', 'done'))

    board = models.ForeignKey(
        Board, related_name='tasks', on_delete=models.CASCADE)

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    status = models.CharField(max_length=20, choices=STATUS, default='to-do')
    priority = models.CharField(
        max_length=10, choices=PRIORITY, default='medium')

    assignee = models.ForeignKey(User, related_name='assigned_tasks',
                                 null=True, blank=True, on_delete=models.SET_NULL)
    reviewer = models.ForeignKey(User, related_name='reviewing_tasks',
                                 null=True, blank=True, on_delete=models.SET_NULL)

    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title