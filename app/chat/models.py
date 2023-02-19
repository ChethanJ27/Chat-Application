from django.contrib.auth.models import User
from django.db import models

class Room(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=128,unique=True)
    online = models.ManyToManyField(to=User, blank=True)

    def get_online_count(self):
        return self.online.count()
    
    def join(self, user):
        self.online.add(user)
        self.save()

    def leave(self, user):
        self.online.remove(user)
        self.save()

    def __str__(self) -> str:
        return f'{self.name} ({self.get_online_count()})'
    

class Message(models.Model):
    user = models.ForeignKey(to=User,on_delete=models.CASCADE)
    Room = models.ForeignKey(to=Room,on_delete=models.CASCADE)
    content = models.CharField(max_length=512)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username}: {self.content} [{self.timestamp}]'