from django.urls import path
from . import views
from .views import CustomSignupView

urlpatterns = [
    path("", views.landing_page, name="landing"),
    path('accounts/signup/', CustomSignupView.as_view(), name='account_signup'),
    path("home/", views.home, name='home'),

    # Profile URLs
    path('profile/', views.profile, name='user_profile'),
    path('profile/<str:username>/', views.profile, name='profile'),
    path('edit_profile/', views.edit_profile, name='edit_profile'),

    # Location & Gallery
    path('save_location/', views.save_location, name='save_location'),
    path('get-gallery-images/<int:user_id>/',
         views.get_gallery_images, name='get_gallery_images'),
    path("gallery/", views.gallery_form, name="gallery_form"),

    # Likes / Matches
    path('who-liked-me/', views.who_liked_me, name='who_liked_me'),
    path('like-back/<int:user_id>/', views.like_back, name='like_back'),
    path('like/<int:user_id>/', views.like_user, name='like_profile'),
    path('dislike/<int:user_id>/', views.dislike_user, name='dislike_user'),

    # Swipe & Matches pages

    path('matches/', views.get_potential_matches, name='match_results'),
    path("matches/", views.matched_users_view, name="matched_users_view"),

    # Duplicate removed
    path("update_location/", views.save_location, name="update_location"),
    path('terms/', views.terms, name='terms'),
    path('privacy/', views.privacy, name='privacy'),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    path('delete-profile/', views.delete_profile, name='delete_profile'),
]
