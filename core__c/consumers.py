import json
import jwt
from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.generic.websocket import AsyncJsonWebsocketConsumer

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
        """
        Handle new WebSocket connection.
        Authenticates the user via JWT access token passed in query string,
        and connects them to a chat room with the target user (roomName = other user's ID).
        """
        # Parse token and target user from query string
        query_string = self.scope['query_string'].decode('utf-8')
        query_params = parse_qs(query_string)
        token = query_params.get('token', [None])[0]
        print(f"Token: {token}")
        target_user_id = query_params.get('roomName', [None])[0]

        # Validate presence of required params
        if not token or not target_user_id:
            await self.close(code=4001)  # Missing token or target
            print("Here rejecting")
            return

        try:
            # Decode JWT access token
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            user_id = payload.get('user_id')
            if not user_id:
                raise ValueError("user_id not found in token")

            # Get the authenticated user (sender)
            sender = await self.get_user_by_id(user_id)
            if not sender:
                raise ValueError("Sender user not found")

            # Get the receiver (target user)
            receiver = await self.get_user_by_id(target_user_id)
            if not receiver:
                raise ValueError("Target user not found")

            # Generate unique chatroom name based on both user IDs
            self.chatroom = self.generate_chatroom(sender, receiver)

            # Get or create the thread object
            print("Here i",)
            self.thread = await self.get_thread(sender, receiver)
            print("Here ii",)

            # Join the user to the group
            await self.channel_layer.group_add(self.chatroom, self.channel_name)
            await self.accept()

            # Send chat history
            chat_history = await self.fetch_chat_history(self.thread)
            await self.send_json({
                "type": "chat_history",
                "messages": chat_history
            })

        except jwt.ExpiredSignatureError:
            await self.close(code=4002)  # Token expired
        except jwt.InvalidTokenError:
            await self.close(code=4003)  # Invalid token
        except ValueError:
            await self.close(code=4004)  # User-related error
        except Exception:
            await self.close(code=4005)  # Unexpected error

    @database_sync_to_async
    def get_user_by_id(self, user_id):
        """Fetch a user by ID, return None if not found."""
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

    def generate_chatroom(self, user1, user2):
        """
        Generate a unique, deterministic chatroom name for a user pair.
        Ensures both users always get the same room name.
        """
        ids = sorted([str(user1.id), str(user2.id)])
        return f"chat_{ids[0]}_{ids[1]}"

    @database_sync_to_async
    def get_thread(self, user1, user2):
        """
        Fetch or create a chat thread between two users.
        Implement your own model-based logic here.
        """
        from .models import ChatThread  # Replace with your model
        thread, _ = ChatThread.objects.get_or_create(primary_user=user1, secondary_user=user2)
        return thread

    @database_sync_to_async
    def fetch_chat_history(self, thread):
        """
        Retrieve previous messages in the thread.
        Customize this method based on your model.
        """
        from .models import Chatmessage  # Replace with your model
        messages = Chatmessage.objects.filter(thread=thread).order_by('message_time')

        return [
            {
                "sender": msg.sender.username,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat()
            }
            for msg in messages
        ]
    
    async def receive(self, text_data):
        """
        Handles incoming WebSocket messages. Supported types:
        - chat_message: Sends chat text to recipient
        - email: Sends an email with optional attachment
        - file: Sends a file to recipient via WebSocket
        """
        # Ensure the incoming message is valid JSON
        if not text_data.strip():
            await self.send(text_data=json.dumps({
                "error": "Empty message received"
            }))
            return
    
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                "error": "Invalid JSON data received"
            }))
            return
    
        message_type = data.get("type")
        to_user = data.get("to_user")
    
        # Route based on message type
        if message_type == "chat_message":
            await self.handle_chat_message(data, to_user)
    
        elif message_type == "email":
            await self.send_email_with_attachments(
                subject=data.get("subject", "No Subject"),
                body=data.get("message", ""),
                to_email=to_user,
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
                        "to_user": to_user,
                    },
                )
            else:
                await self.send(text_data=json.dumps({
                    "error": "File upload failed"
                }))
    
        else:
            await self.send(text_data=json.dumps({
                "error": "Unsupported message type"
            }))

    async def handle_chat_message(self, data, to_user):
        """
        Broadcasts a chat message to the group.
        """
        await self.channel_layer.group_send(
            self.chatroom,
            {
                "type": "chat_message",
                "message": data.get("message", ""),
                "from_user": self.scope["user"].username,
                "to_user": to_user,
            },
        )
    
    
    
    async def send_email_with_attachments(self, subject, body, to_email, file_name=None, file_data=None):
        """
        Sends an email with optional attachment.
        """
        email = EmailMessage(
            subject=subject,
            body=body,
            from_email="no-reply@example.com",
            to=[to_email],
        )

        if file_name and file_data:
            file_bytes = base64.b64decode(file_data)
            email.attach(file_name, file_bytes)

        email.send()

    async def handle_file_upload(self, file_name, file_data, file_type=None):
        """
        Decodes base64 file data and saves it to default storage.
        Returns the saved file path (URL or path).
        """
        if not file_name or not file_data:
            return None

        # Decode the base64 string
        file_bytes = base64.b64decode(file_data)
        file_content = ContentFile(file_bytes, name=file_name)

        # Save the file using Django's default storage
        file_path = default_storage.save(f"uploads/{file_name}", file_content)

        # If using a media server (e.g., Cloudinary or S3), return the URL here
        return default_storage.url(file_path)

    async def chat_message(self, event):
        """
        Sends a chat message to WebSocket.
        """
        await self.send(text_data=json.dumps({
            "type": "chat_message",
            "message": event["message"],
            "from_user": event["from_user"],
            "to_user": event["to_user"],
        }))

    async def file_message(self, event):
        """
        Sends file message to WebSocket.
        """
        await self.send(text_data=json.dumps({
            "type": "file",
            "file_url": event["file_url"],
            "from_user": event["from_user"],
            "to_user": event["to_user"],
        }))
    