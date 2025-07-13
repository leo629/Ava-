import json
import re
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import User
from .models import Message
from channels.db import database_sync_to_async
from django.utils import timezone


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        self.username = self.scope['url_route']['kwargs']['username']
        safe_username = re.sub(r'[^a-zA-Z0-9\-\._]', '_', self.username)
        self.room_group_name = f"chat_{safe_username}"

        await self.set_user_online()
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        await self.mark_messages_as_read()

    async def disconnect(self, close_code):
        await self.set_user_offline()
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        receiver_username = data['receiver']
        sender = self.scope['user']

        receiver = await self.get_user(receiver_username)
        saved_message = await self.create_message(sender, receiver, message)

        await self.channel_layer.group_send(
             self.room_group_name,
      {
        'type': 'chat_message',
        'message': message,
        'sender': sender.username,
        'is_read': saved_message.is_read,
        'id': saved_message.id,
    }
)


    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender': event['sender'],
            'is_read': event['is_read'],
            'id': event['id'],
        }))

    async def read_receipts(self, event):
        await self.send(text_data=json.dumps({
            'type': 'read_receipt',
            'message_ids': event['message_ids'],
        }))

    @database_sync_to_async
    def get_user(self, username):
        return User.objects.get(username=username)

    @database_sync_to_async
    def create_message(self, sender, receiver, message):
        return Message.objects.create(sender=sender, receiver=receiver, message=message)

    @database_sync_to_async
    def get_unread_messages(self):
        return list(Message.objects.filter(sender__username=self.username, receiver=self.user, is_read=False))

    @database_sync_to_async
    def mark_all_as_read(self):
        messages = Message.objects.filter(sender__username=self.username, receiver=self.user, is_read=False)
        messages.update(is_read=True)
        return list(messages.values_list('id', flat=True))

    @database_sync_to_async
    def set_user_online(self):
        if hasattr(self.user, 'profile'):
            self.user.profile.is_online = True
            self.user.profile.save()

    @database_sync_to_async
    def set_user_offline(self):
        if hasattr(self.user, 'profile'):
            self.user.profile.is_online = False
            self.user.profile.last_seen = timezone.now()
            self.user.profile.save()

    async def mark_messages_as_read(self):
        message_ids = await self.mark_all_as_read()
        if message_ids:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'read_receipts',
                    'message_ids': message_ids,
                }
            )
