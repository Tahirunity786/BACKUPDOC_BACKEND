from django.db import models
from django.utils.crypto import get_random_string
from django.utils.timezone import now
from core__a.models import User
from django.db.models import Q


class ThreadManager(models.Manager):
    def by_user(self,**kwargs):
        user = kwargs.get('user')
        lookup = Q(primary_user=user) | Q(secondary_user=user)
        qs = self.get_queryset().filter(lookup).distinct()
        return qs

class ChatThread(models.Model):
    primary_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_primary_user')
    secondary_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_secondary_user')
    primary_last_message_time = models.DateTimeField(null=True, blank=True)
    secondary_last_message_time = models.DateTimeField(null=True, blank=True)
    objects = ThreadManager()

    class Meta:
        unique_together = ['primary_user', 'secondary_user']

class Chatmessage(models.Model):
    thread = models.ForeignKey(ChatThread, on_delete=models.CASCADE, related_name='chatmessage_thread')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    message_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['message_time']