# chat/consumers.py
import json

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from .models import Room, Message
from django.contrib.auth.models import User


class ChatConsumer(WebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.room_name = None
        self.room_group_name = None
        self.room = None
        self.user = None
        self.user_inbox = None

    def connect(self):
        email_address = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_name = email_address.replace('.', '_').replace('@', '-')
        self.room_group_name = f'chat_{self.room_name}'
        self.room, created = Room.objects.get_or_create(name=self.room_name)
        self.user = User.objects.get(email=email_address)

        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name,
        )

        self.user_inbox = f'inbox_{self.user.username}'
        
        self.accept()

        # send the user list to the newly joined user
        self.send(json.dumps({
            'type': 'user_list',
            'users': [user.username for user in self.room.online.all()],
        }))

        if self.user.is_authenticated:
            # send the join event to the room
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'user_join',
                    'user': self.user.username,
                }
            )
            print("authenticated")
            self.room.online.add(self.user)

            # create a user inbox for private messages
            async_to_sync(self.channel_layer.group_add)(
                self.user_inbox,
                self.channel_name,
            )

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name, 
            self.channel_name,
        )
        
        if self.user.is_authenticated:
            # send the leave event to the room
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'user_leave',
                    'user': self.user.username,
                }
            )
            self.room.online.remove(self.user)

            # delete the user inbox for private messages
            async_to_sync(self.channel_layer.group_discard)(
                self.user_inbox,
                self.channel_name,
            )

     # Receive message from WebSocket
    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']


        if not self.user.is_authenticated:
            return
        
        if message.startswith('/pm '):
            recipient_username = text_data_json['recipient']
            # get the recipient user object
            recipient_user = User.objects.get(username=recipient_username)

            # check if the recipient is online
            channel_layer = get_channel_layer()
            recipient_channel = channel_layer.group_channels(f'inbox_{recipient_username}')
            is_recipient_online = len(recipient_channel) > 0

            # send message to recipient if they are online
            if is_recipient_online:
                async_to_sync(channel_layer.group_send)(
                    f'inbox_{recipient_username}',
                    {
                        'type': 'private_message',
                        'sender': self.user.username,
                        'message': message
                    }
                )

            # # send private message delivered to the user
            # self.send(json.dumps({
            #     'type': 'private_message_delivered',
            #     'target': target,
            #     'message': target_msg,
            # }))

            Message.objects.create(user=self.user, room= self.room, content=message)
            return

        # Send message to room group
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name, 
            {
                "type": "chat_message",
                "user": self.user.username,
                "message": message
            }
        )
        Message.objects.create(user=self.user, room= self.room, content=message)

    # Receive message from room group
    def chat_message(self, event):
        message = event["message"]

        # Send message to WebSocket
        self.send(text_data=json.dumps({"message": message}))

    def user_join(self, event):
        self.send(text_data=json.dumps(event))

    def user_leave(self, event):
        self.send(text_data=json.dumps(event))

    def private_message(self, event):
        self.send(text_data=json.dumps(event))

    def private_message_delivered(self, event):
        self.send(text_data=json.dumps(event))