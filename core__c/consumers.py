import json
import uuid
import jwt
from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.layers import get_channel_layer
import aioredis
from django.core.cache import cache
from django_redis import get_redis_connection

from django.conf import settings
from django.db.models import Q
import logging
import base64
import imghdr
import os
from django.core.mail import EmailMessage
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from core__c.serializers import ChatMessageSerializer
from .models import ChatThread, Chatmessage
from core__a.models import User
from urllib.parse import parse_qs
logger = logging.getLogger(__name__)


# class NotificationConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         user = self.scope.get('user')
    
#         if user is None or user.is_anonymous:
#             await self.close(code=4001)  # Unauthorized
#             return
    
#         self.group_name = f'notifications_{user.id}'
    
#         await self.channel_layer.group_add(
#             self.group_name,
#             self.channel_name
#         )
#         await self.accept()
    
        
#     @sync_to_async
#     def get_user_by_cookie(self, user_id):
#         try:
#             token = AnonymousCookies.objects.get(cookie=user_id)
#             return token.user
#         except AnonymousCookies.DoesNotExist:
#             return None
        

#     async def disconnect(self, close_code):
#         if self.group_name:  # Check if group_name is set
#             await self.channel_layer.group_discard(
#                 self.group_name,
#                 self.channel_name
#             )

#     async def send_notification(self, event):
#         await self.send(text_data=json.dumps(event['message']))


class ChatConsumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        query_string = self.scope['query_string'].decode('utf-8')
        query_params = parse_qs(query_string)
        token = query_params.get('token', [None])[0]
        target_user_id = query_params.get('roomName', [None])[0]
        print("Connecting to chat consumer with token:", token)
        print("Connecting to chat consumer with target_user_id:", target_user_id)

        if not token or not target_user_id:
            await self.close(code=4001)
            return

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            user_id = payload.get('user_id')
            if not user_id:
                raise ValueError("user_id not found in token")
        
            sender = await self.get_user_by_id(user_id)
            receiver = await self.get_user_by_id(target_user_id)
        
            if not sender or not receiver:
                raise ValueError("Invalid users")
        
            self.scope["user"] = sender
            self.chatroom = self.generate_chatroom(sender, receiver)
            print("Chatroom name:", self.chatroom)
            self.thread = await self.get_thread(sender, receiver)
        
            await self.channel_layer.group_add(self.chatroom, self.channel_name)
            await self.accept()
        
            chat_history = await self.fetch_chat_history(self.thread)
            await self.send_json({
                "type": "chat_history",
                "messages": chat_history
            })

        except jwt.ExpiredSignatureError:
            await self.close(code=4002)
        except jwt.InvalidTokenError:
            await self.close(code=4003)
        except Exception as e:
            print("Connection error:", str(e))
            await self.close(code=4005)


    async def disconnect(self, close_code):
        if hasattr(self, 'chatroom'):
            await self.channel_layer.group_discard(self.chatroom, self.channel_name)
    

    @database_sync_to_async
    def get_user_by_id(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

    def generate_chatroom(self, user1, user2):
        ids = sorted([str(user1.id), str(user2.id)])
        return f"chat_{ids[0]}_{ids[1]}"

    @database_sync_to_async
    def get_thread(self, user1, user2):
        from .models import ChatThread
        # Sort users by id to ensure consistency
        primary_user, secondary_user = sorted([user1, user2], key=lambda u: u.id)
        thread, _ = ChatThread.objects.get_or_create(
            primary_user=primary_user,
            secondary_user=secondary_user
        )
        return thread

    @database_sync_to_async
    def fetch_chat_history(self, thread):
        from .models import Chatmessage
        messages = Chatmessage.objects.filter(thread=thread).order_by('message_time')
        return [
            {
                "sender": msg.user.username,
                "content": msg.message,
                "timestamp": msg.message_time.isoformat()
            } for msg in messages
        ]

    async def receive(self, text_data):
        if not text_data:
            await self.send_json({"error": "Empty message received"})
            return

        try:
            data = json.loads(text_data)
        except json.JSONDecodeError as e:
            await self.send_json({"error": f"Invalid JSON: {str(e)}"})
            return

        if not isinstance(data, dict):
            await self.send_json({"error": "Expected a JSON object"})
            return

        message_type = data.get("type")
        to_user_id = data.get("to_user")

        if message_type == "chat_message":
            await self.handle_chat_message(data, to_user_id)
        elif message_type == "email":
            await self.send_email_with_attachments(
                subject=data.get("subject", "No Subject"),
                body=data.get("message", ""),
                to_email=to_user_id,
                file_name=data.get("file_name"),
                file_data=data.get("file_data")
            )
        elif message_type == "file":
            saved_path = await self.handle_file_upload(
                file_name=data.get("file_name"),
                file_data=data.get("file_data"),
                file_type=data.get("file_type")
            )
            if saved_path:
                await self.channel_layer.group_send(
                    self.chatroom,
                    {
                        "type": "file_message",
                        "file_url": saved_path,
                        "from_user": self.scope["user"].username,
                        "to_user": to_user_id,
                    }
                )
            else:
                await self.send_json({"error": "File upload failed"})
        else:
            await self.send_json({"error": f"Unsupported message type: {message_type}"})

    async def handle_chat_message(self, data, to_user_id):
        message_text = data.get("message", "").strip()
        if not message_text:
            await self.send_json({"error": "Message cannot be empty."})
            return

        from_user = self.scope["user"]
        thread = self.thread

        # Save message to DB
        await self.save_message(thread, from_user, message_text)
        await self.update_last_message_time(thread, from_user)

        # Send message to WebSocket group
        await self.channel_layer.group_send(
            self.chatroom,
            {
                "type": "chat_message",
                "message": message_text,
                "from_user": from_user.username,
                "from_user_id": from_user.id,
                "to_user": to_user_id,
            }
        )


    @database_sync_to_async
    def save_message(self, thread, sender, message):
        from .models import Chatmessage
        msg = Chatmessage.objects.create(
            thread=thread,
            user=sender,
            message=message,
            message_id=str(uuid.uuid4())  # Add this field to model if not present
        )
        return msg
    
    @database_sync_to_async
    def update_last_message_time(self, thread, sender):
        from django.utils import timezone
        now = timezone.now()
        if thread.primary_user == sender:
            thread.primary_last_message_time = now
        else:
            thread.secondary_last_message_time = now
        thread.save(update_fields=["primary_last_message_time", "secondary_last_message_time"])

    async def send_email_with_attachments(self, subject, body, to_email, file_name=None, file_data=None):
        email = EmailMessage(subject=subject, body=body, from_email="no-reply@example.com", to=[to_email])
        if file_name and file_data:
            try:
                file_bytes = base64.b64decode(file_data)
                email.attach(file_name, file_bytes)
            except Exception as e:
                await self.send_json({"error": f"Attachment error: {str(e)}"})
        email.send()

    async def handle_file_upload(self, file_name, file_data, file_type=None):
        if not file_name or not file_data:
            return None
        try:
            file_bytes = base64.b64decode(file_data)
            file_content = ContentFile(file_bytes, name=file_name)
            file_path = default_storage.save(f"uploads/{file_name}", file_content)
            return default_storage.url(file_path)
        except Exception as e:
            print("File upload error:", e)
            return None

    async def chat_message(self, event):
        await self.send_json({
            "type": "chat_message",
            "message": event["message"],
            "from_user": event["from_user"],
            "from_user_id": event["from_user_id"],
            "to_user": event["to_user"],
        })
    

    async def file_message(self, event):
        await self.send_json({
            "type": "file",
            "file_url": event["file_url"],
            "from_user": event["from_user"],
            "to_user": event["to_user"],
        })
