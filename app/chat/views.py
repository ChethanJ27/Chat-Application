from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from rest_framework.response import  Response
from .models import Message
from .utils import createRoomId
from rest_framework import generics,status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated


def index(request):
    return render(request, "chat/index.html")

def room(request, room_name):
    return render(request, "chat/room.html", {"room_name": room_name})


class History(APIView):
    permission_classes = [IsAuthenticated, ]

    def post(request):
        print(request)
        user2_email = request.query_params.get('email')
        print(user2_email)
        user = request.user
        print(user)
        curr_user_email = user.email
        room_id = createRoomId(user1_email=curr_user_email,user2_email=user2_email)
        print(room_id)
        query = 'SELECT * from recipe_recipe where Room > %s limit 100 ' %room_id
        queryset = Message.objects.raw(query)
        print(queryset)
        return Response(status=status.HTTP_401)
    