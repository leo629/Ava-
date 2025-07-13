from django.urls import path
from .views import chat_room, home, chat_list
from . import views

urlpatterns = [
    path("chat/<str:username>/", chat_room, name="chat_room"),
    path('', home, name='home'),
    path('messages/', chat_list, name='chat_list'),
]
