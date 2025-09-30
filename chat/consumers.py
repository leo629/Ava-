import json
import re
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import User
from .models import Message
from channels.db import database_sync_to_async
from django.utils import timezone
from notifications.views import send_notification


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        self.username = self.scope['url_route']['kwargs']['username']
        safe_username = re.sub(r'[^a-zA-Z0-9\-\._]', '_', self.username)
        self.room_group_name = f"chat_{safe_username}"

        # Set user online
        await self.set_user_online()

        # Join the room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        # Accept the WebSocket connection
        await self.accept()

        # Mark unread messages as read and send read receipts
        message_ids = await self.mark_all_as_read()
        if message_ids:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'read_receipts',
                    'message_ids': message_ids
                }
            )

    async def disconnect(self, close_code):
        # Set user offline
        await self.set_user_offline()

        # Leave the room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)

            if data.get('action') == 'mark_read':
                message_ids = await self.mark_all_as_read()
                if message_ids:
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {'type': 'read_receipts', 'message_ids': message_ids}
                    )
            else:
                message = data['message']
                receiver_username = data['receiver']
                sender = self.scope['user']
                receiver = await self.get_user(receiver_username)
                saved_message = await self.create_message(sender, receiver, message)

                # Send notification to receiver
                await database_sync_to_async(send_notification)(
                    sender=sender,
                    recipient=receiver,
                    notification_type='message',
                    message=f"{sender.username} sent you a message!"
                )

                # Broadcast message to the group
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
        except Exception as e:
            await self.send(text_data=json.dumps({'error': str(e)}))

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
        import bleach
        cleaned_message = bleach.clean(
            message, tags=['p', 'strong', 'em'], strip=True)
        return Message.objects.create(sender=sender, receiver=receiver, message=cleaned_message[:1000])

    @database_sync_to_async
    def mark_all_as_read(self):
        messages = Message.objects.filter(
            sender__username=self.username, receiver=self.user, is_read=False)
        message_ids = list(messages.values_list('id', flat=True))
        messages.update(is_read=True)
        return message_ids

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
