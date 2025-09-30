from django.urls import path
from . import views

urlpatterns = [
    path('all/', views.notification_list, name='notification_list'),
    path('fetch/', views.fetch_notifications, name='fetch_notifications'),
    path('mark-read/', views.mark_notifications_read,
         name='mark_notifications_read'),
]
