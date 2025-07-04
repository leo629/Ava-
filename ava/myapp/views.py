from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.urls import reverse
from .forms import CustomSignupForm, ProfileForm, GalleryForm, EditProfileForm
from .models import Profile, Gallery, Match, Like
from allauth.account.views import SignupView
from geopy.distance import geodesic
from django.views.decorators.csrf import csrf_exempt
import json
from notifications.views import send_notification
import random


@csrf_exempt
@login_required
def like_user(request, user_id):
    other = get_object_or_404(User, id=user_id)
    Like.objects.get_or_create(from_user=request.user, to_user=other)

    if Like.objects.filter(from_user=other, to_user=request.user).exists():
        Match.objects.get_or_create(
            user=request.user, target=other, liked=True)
        Match.objects.get_or_create(
            user=other, target=request.user, liked=True)

        send_notification(sender=request.user, recipient=other, notification_type='match',
                          message=f"You and {request.user.username} matched!")

    return JsonResponse({"status": "liked"})


@csrf_exempt
@login_required
def dislike_user(request, user_id):
    other = get_object_or_404(User, id=user_id)
    Like.objects.filter(from_user=request.user, to_user=other).delete()
    Match.objects.filter(user=request.user, target=other).delete()
    Match.objects.filter(user=other, target=request.user).delete()

    return JsonResponse({"status": "disliked"})


@login_required
def get_gallery_images(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        images = [request.build_absolute_uri(
            img.image.url) for img in user.gallery.all()]
        return JsonResponse({'images': images})
    except User.DoesNotExist:
        return JsonResponse({'images': []})


@login_required
def swipe_page(request):
    profiles = Profile.objects.exclude(user=request.user)

    swipe_data = []
    for profile in profiles:
        gallery_images = list(profile.user.gallery.all())
        if gallery_images:
            image = random.choice(gallery_images).image.url
        else:
            image = profile.profile_pic.url if profile.profile_pic else '/static/img/default.jpg'

        swipe_data.append({
            'id': profile.user.id,
            'name': profile.user.username,
            'age': profile.age,
            'location': profile.city,
            'image': image,
        })

    return render(request, 'swipe/swipe_page.html', {'swipe_data': swipe_data})


@login_required
def who_liked_me(request):
    likes = Match.objects.filter(
        target=request.user, liked=True
    ).exclude(
        user__in=Match.objects.filter(
            user=request.user).values_list('target', flat=True)
    )
    return render(request, 'myapp/who_liked_me.html', {'likes': likes})


@login_required
def like_back(request, user_id):
    other_user = get_object_or_404(User, id=user_id)
    Match.objects.get_or_create(
        user=request.user, target=other_user, liked=True)

    if Match.objects.filter(user=other_user, target=request.user, liked=True).exists():
        send_notification(sender=request.user, recipient=other_user, notification_type='match',
                          message=f"You and {request.user.username} matched!")

    return redirect('who_liked_me')


@csrf_exempt
@login_required
def save_location(request):
    if request.method == "POST":
        data = json.loads(request.body)
        lat = data.get("latitude")
        lng = data.get("longitude")

        profile = request.user.profile
        profile.latitude = lat
        profile.longitude = lng
        profile.save()

        return JsonResponse({"status": "success"})
    return JsonResponse({"error": "Invalid request"}, status=400)


class CustomSignupView(SignupView):
    form_class = CustomSignupForm
    template_name = 'myapp/signup.html'

    def get_success_url(self):
        return reverse('home')  # Redirect to home after signup


def register(request):
    if request.method == 'POST':
        form = CustomSignupForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(request)
            login(request, user)
            # Redirect to home after manual registration
            return redirect('home')
    else:
        form = CustomSignupForm()
    return render(request, 'myapp/register.html', {'form': form})


@login_required
def profile(request, username=None):
    user = get_object_or_404(
        User, username=username) if username else request.user
    profile = user.profile
    gallery_images = Gallery.objects.filter(user=user)
    return render(request, 'myapp/profile.html', {
        'profile_user': user,
        'profile': profile,
        'gallery_images': gallery_images
    })


def is_mutual_match(user1, user2):
    return (
        Match.objects.filter(user=user1, target=user2, liked=True).exists() and
        Match.objects.filter(user=user2, target=user1, liked=True).exists()
    )


@login_required
def profile_view(request, username):
    user = get_object_or_404(User, username=username)
    profile = user.profile
    gallery_images = Gallery.objects.filter(user=user)

    return render(request, 'myapp/profile.html', {
        'profile_user': user,
        'profile': profile,
        'gallery_images': gallery_images
    })


@login_required
def edit_profile(request):
    profile = request.user.profile
    if request.method == 'POST':
        edit_form = EditProfileForm(
            request.POST, request.FILES, instance=profile)
        gallery_form = GalleryForm(request.POST, request.FILES)
        if edit_form.is_valid():
            edit_form.save()
        if gallery_form.is_valid():
            new_image = gallery_form.save(commit=False)
            new_image.user = request.user
            new_image.save()
        return redirect('edit_profile')
    else:
        edit_form = EditProfileForm(instance=profile)
        gallery_form = GalleryForm()

    user_gallery = Gallery.objects.filter(user=request.user)

    return render(request, 'myapp/edit_profile.html', {
        'edit_form': edit_form,
        'gallery_form': gallery_form,
        'user_gallery': user_gallery
    })


@login_required
def home(request):
    users = User.objects.exclude(username=request.user.username)
    return render(request, 'myapp/home.html', {'users': users})


@login_required
def matched_users_view(request):
    user = request.user

    matched_user_ids = Match.objects.filter(
        user=user, liked=True).values_list('target', flat=True)
    matched_back = Match.objects.filter(
        user__in=matched_user_ids, target=user, liked=True).values_list('user', flat=True)

    mutual_matches = User.objects.filter(id__in=matched_back)

    return render(request, 'myapp/matched_users.html', {'matches': mutual_matches})


@login_required
def match_results(request):
    matches = []
    user_profile = request.user.profile

    for profile in Profile.objects.exclude(user=request.user):
        if profile.age and user_profile.age:
            age_diff = abs(profile.age - user_profile.age)
            if age_diff > 5:
                continue

        if profile.latitude and profile.longitude and user_profile.latitude and user_profile.longitude:
            distance = geodesic(
                (user_profile.latitude, user_profile.longitude),
                (profile.latitude, profile.longitude)
            ).km
            if distance > 100:
                continue
        else:
            distance = None

        # Get random image from gallery or fallback to profile_pic
        gallery_images = Gallery.objects.filter(user=profile.user)
        if gallery_images.exists():
            image_url = random.choice(list(gallery_images)).image.url
        elif profile.profile_pic:
            image_url = profile.profile_pic.url
        else:
            image_url = '/static/img/default.jpg'

        matches.append({
            'username': profile.user.username,
            'age': profile.age,
            'city': profile.city,
            'image': image_url,
            'distance': round(distance, 1) if distance else "Unknown"
        })

    return render(request, 'myapp/matches.html', {'matches': matches})


# ✅ Helper function (no @login_required)
def get_potential_matches(user):
    user_profile = user.profile
    candidates = Profile.objects.exclude(user=user)

    matches = []
    for profile in candidates:
        if profile.age and user_profile.age:
            age_diff = abs(profile.age - user_profile.age)
            if age_diff > 5:
                continue

        if profile.latitude and profile.longitude and user_profile.latitude and user_profile.longitude:
            distance = geodesic(
                (user_profile.latitude, user_profile.longitude),
                (profile.latitude, profile.longitude)
            ).km
            if distance <= 100:
                matches.append(profile)

    return matches
