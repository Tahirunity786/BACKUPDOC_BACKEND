# views.py
from datetime import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils.timezone import make_aware
from .models import ChatThread, Chatmessage
from django.contrib.auth import get_user_model
User = get_user_model()

class ChatListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        threads = ChatThread.objects.by_user(user=user)
        
        chat_list = []
        for thread in threads:
            # Identify the other user
            other_user = thread.secondary_user if thread.primary_user == user else thread.primary_user
            
            # Get latest message
            last_message = Chatmessage.objects.filter(thread=thread).order_by('-message_time').first()
            last_msg_time = last_message.message_time if last_message else None
            last_msg_text = last_message.message if last_message else ""

            chat_list.append({
                "user_id": other_user.id,
                "name": f'{other_user.first_name} {other_user.last_name}',
                "lastMessage": last_msg_text,
                "lastMessageTime": last_msg_time,
                "imgId": other_user.id % 70 + 1,
            })

        chat_list = sorted(
            chat_list, 
            key=lambda x: x["lastMessageTime"] or make_aware(datetime.min), 
            reverse=True
)

        return Response(chat_list)
