from django.urls import path
from home.views import *

urlpatterns = [
    path("", chat, name='chat_room'),
    path("<str:room_name>/", room, name="room"),
]