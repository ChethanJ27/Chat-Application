# chat/consumers.py
import json

from asgiref.sync import async_to_sync, sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer, WebsocketConsumer
from channels.db import database_sync_to_async
from .models import Room, Message
from django.contrib.auth.models import User
from .utils import createRoomId
from rest_framework.authtoken.models import Token

tokenIndex = 0

class ChatConsumer(AsyncWebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.room_name = None
        self.room_group_name = None
        self.room = None
        self.user = None
        self.user_inbox = None

    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f'chat_{self.room_name}'
        self.room, created = await sync_to_async(Room.objects.get_or_create)(name=self.room_name)
        
        # Extract the token from the query string
        # token = self.scope["query_string"].decode().split("=")[1]
        global tokenIndex
        tokens = ["e5e775f6d3220629a3184773037b325fc832c2bb","9c2b613f19abba8c3342b03e0f4c8c6441ecd241"]
        token = tokens[tokenIndex]
        print('tokenIndex',tokenIndex,token)
        tokenIndex = (tokenIndex + 1) % len(tokens)
        print(tokenIndex)
        
        # Authenticate the user
        self.user = await self.get_user(token)
        if self.user is None:
            # Close the WebSocket connection if authentication fails
            await self.close()
        

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )
        print('user added to group',self.room_group_name,self.channel_name)
        
        # Accept the WebSocket connection
        await self.accept()
        print('connect method completed')
        

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name, 
            self.channel_name,
        )
        

     # Receive message from WebSocket
    async def receive(self, text_data):
        print('in recieve method')
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        if not self.user.is_authenticated:
            return
        
        print('before group send',self.user.email)
        print('group name',self.channel_layer)
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'username': self.scope['user'].username
            }
        )
        print('before msg db save')
        await database_sync_to_async(Message.objects.create)(user=self.user, Room= self.room, content=message)
        print('recieve method completed')

    # Receive message from room group
    async def chat_message(self, event):
        print('in send method')
        message = event['message']
        username = event['username']
        await self.send(text_data=json.dumps({
            'message': message,
            'username': username
        }))
        print('send method completed')


    def user_join(self, event):
        self.send(text_data=json.dumps(event))

    def user_leave(self, event):
        self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def get_user(self, token):
        try:
            # Get the user associated with the token
            token_obj = Token.objects.get(key=token)
            user = User.objects.get(id=token_obj.user_id)
            return user
        except Token.DoesNotExist:
            return None


class PersonalChats(WebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.room_name = None
        self.room_group_name = None
        self.room = None
        self.user = None
        self.user_inbox = None

    def connect(self):
        email_address = self.scope["url_route"]["kwargs"]["room_name"]
        self.user = self.scope['user']
        if not self.user.is_authenticated:
            return
        user1_email = self.user.email
        self.room_name = createRoomId(user1_email=user1_email, user2_email=email_address)

        self.room_group_name = f'pmchat_{self.room_name}'
        self.room, created = Room.objects.get_or_create(name=self.room_name)

        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name,
        )

        # self.user_inbox = f'inbox_{self.user.username}'
        
        self.accept()

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

    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        if not self.user.is_authenticated:
            return
        
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name, 
            {
                "type": "chat_message",
                "user": self.user.username,
                "message": message
            }
        )
        Message.objects.create(user=self.user, room= self.room, content=message)
        return
    
    def chat_message(self, event):
        message = event["message"]

        # Send message to WebSocket
        self.send(text_data=json.dumps({"message": message}))