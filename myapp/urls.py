from django.urls import path
from . import views
from .views import CustomSignupView

urlpatterns = [
    path('accounts/signup/', CustomSignupView.as_view(), name='account_signup'),
    path('', views.home, name='home'),
    path('profile/', views.profile, name='user_profile'),
    path('profile/<str:username>/', views.profile_view, name='profile'),
    path('edit_profile/', views.edit_profile, name='edit_profile'),
    path('save_location/', views.save_location, name='save_location'),
    path('who-liked-me/', views.who_liked_me, name='who_liked_me'),
    path('like-back/<int:user_id>/', views.like_back, name='like_back'),
    path('get-gallery-images/<int:user_id>/',
         views.get_gallery_images, name='get_gallery_images'),
    path("swipe/", views.swipe_page, name="swipe_page"),
    path("like/<int:user_id>/", views.like_user, name="like_user"),
    path("dislike/<int:user_id>/", views.dislike_user, name="dislike_user"),
    path('matches/', views.match_results, name='match_results'),
    path('matches/', views.get_potential_matches, name='matched_users_view'),
    path("update_location/", views.save_location, name="update_location"),

]
