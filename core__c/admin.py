from django.contrib import admin
from .models import ChatThread ,Chatmessage
# Register your models here.
admin.site.register(ChatThread)
admin.site.register(Chatmessage)