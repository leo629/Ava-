from django.urls import path
from . import views

app_name = "swipes"  # Important!

urlpatterns = [
    path('', views.swipe_page, name='swipe_page'),
    path('action/', views.swipe_action, name='swipe_action'),
]
