from django.conf import settings
from django.core.mail import send_mail
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from geopy.distance import geodesic
import random
import json
from .forms import CustomSignupForm, ProfileForm, GalleryForm, EditProfileForm
from .models import Profile, Gallery, Match, Like
from .utils import calculate_distance
from notifications.views import send_notification
from allauth.account.views import SignupView
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST, require_GET
import maths

User = get_user_model()


def _is_ajax(request):
    return request.headers.get("x-requested-with") == "XMLHttpRequest"


def calculate_distance(lat1, lon1, lat2, lon2):
    """Return distance in km using haversine formula."""
    if None in [lat1, lon1, lat2, lon2]:
        return None

    R = 6371  # Earth radius in KM
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 1)


# -----------------------------
# Save User Location
# -----------------------------
@login_required
@require_POST
def save_location(request):
    lat = request.POST.get("lat")
    lon = request.POST.get("lon")
    city = request.POST.get("city", "")

    if not lat or not lon:
        return JsonResponse({"status": "error", "message": "Missing coordinates"}, status=400)

    profile = request.user.profile
    profile.latitude = lat
    profile.longitude = lon
    if city:
        profile.city = city
    profile.save()

    return JsonResponse({"status": "ok"})


# -----------------------------
# Users Near You (Matches Page)
# -----------------------------
@login_required
def users_near_you(request):
    current_user = request.user
    my_profile = current_user.profile

    # ask for location if missing
    if not my_profile.latitude or not my_profile.longitude:
        return render(request, "ask_location.html")

    # get all profiles except yourself
    profiles = Profile.objects.exclude(user=current_user)

    nearby = []
    for profile in profiles:
        dist = calculate_distance(
            float(my_profile.latitude),
            float(my_profile.longitude),
            float(profile.latitude) if profile.latitude else None,
            float(profile.longitude) if profile.longitude else None,
        )

        if dist is not None:
            profile.distance = dist
            nearby.append(profile)

    # Sort by nearest first
    nearby_sorted = sorted(nearby, key=lambda x: x.distance)

    return render(request, "users_near_you.html", {"profiles": nearby_sorted})


@login_required
def delete_profile(request):
    user = request.user

    if request.method == "POST":
        user.delete()  # deletes the user and cascades to profile
        messages.success(request, "Your profile has been deleted successfully.")
        return redirect("account_signup")  # or home page

    # If GET request, show a confirmation page
    return render(request, "myapp/confirm_delete.html")

def landing_page(request):
    if request.user.is_authenticated:
        return redirect('home')  # 👈
    return render(request, 'myapp/landing.html')


def about(request):
    return render(request, "myapp/about.html")


def contact(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        message = request.POST.get("message")

        # Optional: send email
        send_mail(
            subject=f"New Contact Message from {name}",
            message=message,
            from_email=email,
            recipient_list=[settings.DEFAULT_FROM_EMAIL],
        )

        return render(request, "myapp/contact.html", {"success": True})

    return render(request, "myapp/contact.html")


def terms(request):
    return render(request, 'myapp/terms.html')


def privacy(request):
    return render(request, 'myapp/privacy.html')


# -----------------------------
# LIKE / SUPERLIKE / UNLIKE
# -----------------------------
@login_required
@require_POST
def like_user(request, user_id):
    target = get_object_or_404(User, id=user_id)
    action = request.POST.get("action", "toggle").lower()
    is_super = (action == "superlike")

    if target == request.user:
        return JsonResponse({"status": "error", "message": "Cannot like yourself"}, status=400)

    like_obj, created = Like.objects.get_or_create(
        user=request.user,
        liked_user=target,
        defaults={"is_superlike": is_super}
    )

    # Toggle undo like
    if not created and action == "toggle":
        like_obj.delete()
        Match.objects.filter(user=request.user, target=target).delete()
        Match.objects.filter(user=target, target=request.user).delete()

        if _is_ajax(request):
            return JsonResponse({"status": "ok", "action": "unliked"})

        messages.info(request, "Unlike removed.")
        return redirect("profile", username=target.username)

    # Update superlike flag if changed
    if not created:
        if like_obj.is_superlike != is_super:
            like_obj.is_superlike = is_super
            like_obj.save()

    # Update our match record
    Match.objects.update_or_create(
        user=request.user, target=target, defaults={"liked": True}
    )

    # Check if target also liked you = MATCH!
    if Match.objects.filter(user=target, target=request.user, liked=True).exists():
        send_notification(
            sender=request.user,
            recipient=target,
            notification_type="match",
            message=f"You and {request.user.username} matched!"
        )

    # AJAX response
    if _is_ajax(request):
        return JsonResponse({
            "status": "ok",
            "action": "superliked" if is_super else "liked",
            "target_id": target.id,
            "super": is_super
        })

    messages.success(request, "Liked!")
    return redirect("profile", username=target.username)


# -----------------------------
# DISLIKE (SWIPE LEFT)
# -----------------------------
@login_required
@require_POST
def dislike_user(request, user_id):
    target = get_object_or_404(User, id=user_id)

    Like.objects.filter(user=request.user, liked_user=target).delete()
    Match.objects.filter(user=request.user, target=target).delete()
    Match.objects.filter(user=target, target=request.user).delete()

    if _is_ajax(request):
        return JsonResponse({"status": "ok", "action": "disliked", "target_id": target.id})

    messages.info(request, "User disliked.")
    return redirect("profile", username=target.username)


# -----------------------------
# Swipe Page (Carousel)
# -----------------------------
@login_required
def swipe(request):
    user_profile = request.user.profile

    if not user_profile.latitude or not user_profile.longitude:
        return render(request, "ask_location.html")

    # Exclude: yourself + already liked or disliked
    seen_ids = Like.objects.filter(user=request.user).values_list("liked_user", flat=True)

    profiles = Profile.objects.exclude(user=request.user).exclude(user__id__in=seen_ids)

    # Calculate distances
    for p in profiles:
        p.distance = calculate_distance(
            float(user_profile.latitude),
            float(user_profile.longitude),
            float(p.latitude) if p.latitude else None,
            float(p.longitude) if p.longitude else None,
        )

    return render(request, "swipe.html", {"profiles": profiles})



# ✅ Gallery API
@login_required
def get_gallery_images(request, user_id):
    user = get_object_or_404(User, id=user_id)
    images = [request.build_absolute_uri(
        img.image.url) for img in user.gallery.all()]
    return JsonResponse({'images': images})


# ✅ Who liked me
@login_required
def who_liked_me(request):
    likes = Like.objects.filter(liked_user=request.user)
    return render(request, 'myapp/who_liked_me.html', {'likes': likes})


# ✅ Like back to confirm match
@login_required
def like_back(request, user_id):
    other_user = get_object_or_404(User, id=user_id)

    Match.objects.update_or_create(
        user=request.user, target=other_user, defaults={'liked': True}
    )

    if Match.objects.filter(user=other_user, target=request.user, liked=True).exists():
        send_notification(
            sender=request.user,
            recipient=other_user,
            notification_type='match',
            message=f"You and {request.user.username} matched!"
        )

    return redirect('who_liked_me')


#-----------------
# ✅ Custom Signup
#-----------------

class CustomSignupView(SignupView):
    form_class = CustomSignupForm
    template_name = "myapp/signup.html"
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        # Let allauth handle user + profile creation
        response = super().form_valid(form)

        # Ensure profile is updated (in case your save missed anything)
        user = self.user  # allauth sets this
        profile, created = Profile.objects.get_or_create(user=user)

        # Push cleaned_data into profile (as backup to form.save())
        for field in [
            "bio", "gender", "country", "profile_pic", "date_of_birth",
            "interests", "hobbies", "want_kids", "relationship_goal", "lifestyle"
        ]:
            if field in form.cleaned_data:
                setattr(profile, field, form.cleaned_data.get(field))

        profile.save()

        # Save phone number if you extended AbstractUser
        if hasattr(user, "phone_number") and "phone_number" in form.cleaned_data:
            user.phone_number = form.cleaned_data.get("phone_number")
            user.save()

    def get_success_url(self):
        return reverse_lazy("upload_gallery")


# ✅ Profile view

# ... keep all your imports and existing code above ...


@login_required
def profile(request, username=None):
    user = get_object_or_404(
        User, username=username) if username else request.user
    profile = user.profile
    gallery_images = Gallery.objects.filter(user=user)

    like_count = Like.objects.filter(liked_user=user).count()
    liked = Like.objects.filter(user=request.user, liked_user=user).exists()

    # Dynamic profile completion
    profile_fields = [
        field.name for field in Profile._meta.get_fields()
        if field.concrete and field.name not in ['id', 'user']
    ]
    filled_fields = 0
    for field in profile_fields:
        value = getattr(profile, field)
        # Handle ManyToManyFields
        if hasattr(value, 'all'):
            if value.all().exists():
                filled_fields += 1
        elif value:
            filled_fields += 1
    total_fields = len(profile_fields)
    profile_completion = int(
        (filled_fields / total_fields) * 100) if total_fields > 0 else 0

    # Fetch interests for display
    interests = []
    if hasattr(profile, 'interests'):
        interests = list(profile.interests.all()) if hasattr(
            profile.interests, 'all') else [profile.interests]

    return render(request, 'myapp/profile.html', {
        'profile_user': user,
        'profile': profile,
        'gallery_images': gallery_images,
        'like_count': like_count,
        'liked': liked,
        'profile_completion': profile_completion,
        'interests': interests,
    })


@login_required
def edit_profile(request):
    profile = request.user.profile
    user_gallery = Gallery.objects.filter(user=request.user)

    if request.method == 'POST':
        if 'edit_profile_submit' in request.POST:
            edit_form = EditProfileForm(
                request.POST, request.FILES, instance=profile)
            if edit_form.is_valid():
                edit_form.save()
                messages.success(request, "Profile updated!")
                return redirect('edit_profile')
            gallery_form = GalleryForm()
        elif 'gallery_upload_submit' in request.POST:
            gallery_form = GalleryForm(request.POST, request.FILES)
            if gallery_form.is_valid():
                new_image = gallery_form.save(commit=False)
                new_image.user = request.user
                new_image.save()
                messages.success(request, "Image uploaded!")
                return redirect('edit_profile')
            edit_form = EditProfileForm(instance=profile)
    else:
        edit_form = EditProfileForm(instance=profile)
        gallery_form = GalleryForm()

    # ✅ Profile completion calculation
    fields = [
        profile.bio,
        profile.hobbies,
        profile.country,
        profile.gender,
        profile.interests if isinstance(
            profile.interests, str) else profile.interests.count() if profile.interests else 0,
        profile.relationship_goal,
        profile.lifestyle
    ]
    filled_fields = sum(1 for field in fields if field)
    profile_completion = int((filled_fields / len(fields)) * 100)

    return render(request, 'myapp/edit_profile.html', {
        'edit_form': edit_form,
        'gallery_form': gallery_form,
        'user_gallery': user_gallery,
        'profile_completion': profile_completion
    })


# ✅ Home with nearby users

@login_required
def home(request):
    viewer_profile, created = Profile.objects.get_or_create(user=request.user)
    users = User.objects.exclude(id=request.user.id)  # exclude logged-in user

    min_age = request.GET.get("min_age")
    max_age = request.GET.get("max_age")
    max_distance = request.GET.get("max_distance")

    # Gender-based filtering
    if viewer_profile.gender == 'M':
        users = users.filter(profile__gender='F')  # men see women
    elif viewer_profile.gender == 'F':
        users = users.filter(profile__gender='M')  # women see men

    nearby_users = []

    for u in users:
        profile = u.profile

        # ✅ Age filter
        if min_age and profile.age and profile.age < int(min_age):
            continue
        if max_age and profile.age and profile.age > int(max_age):
            continue

        # ✅ Distance calculation
        if (
            viewer_profile.latitude is not None and viewer_profile.longitude is not None
            and profile.latitude is not None and profile.longitude is not None
        ):
            distance = calculate_distance(
                viewer_profile.latitude, viewer_profile.longitude,
                profile.latitude, profile.longitude
            )
        else:
            distance = None

        # ✅ Distance filter
        if max_distance and distance is not None and distance > int(max_distance):
            continue

        nearby_users.append({
            'user': u,
            'distance': distance,
            'city': profile.city or "Unknown"
        })

    # Sort by distance if available
    nearby_users.sort(
        key=lambda x: x['distance'] if x['distance'] is not None else float(
            'inf')
    )

    # Limit results
    nearby_users = nearby_users[:20]

    return render(request, 'myapp/home.html', {
        "nearby_users": nearby_users
    })

# ✅ Matched users


@login_required
def matched_users_view(request):
    user = request.user

    matched_user_ids = Match.objects.filter(
        user=user, liked=True
    ).values_list('target', flat=True)

    matched_back = Match.objects.filter(
        user__in=matched_user_ids, target=user, liked=True
    ).values_list('user', flat=True)

    mutual_matches = User.objects.filter(id__in=matched_back)

    return render(request, 'myapp/matched_users.html', {'matches': mutual_matches})


# ✅ Suggested matches (age/distance filter)
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

        # pick random gallery image or fallback
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


@login_required
def get_potential_matches(request):
    user_profile = request.user.profile
    candidates = Profile.objects.exclude(user=request.user)

    matches = []
    for profile in candidates:
        # Age difference filter (<=5 years)
        if profile.age and user_profile.age:
            age_diff = abs(profile.age - user_profile.age)
            if age_diff > 5:
                continue

        # Distance filter (<=100 km)
        if profile.latitude and profile.longitude and user_profile.latitude and user_profile.longitude:
            distance = geodesic(
                (user_profile.latitude, user_profile.longitude),
                (profile.latitude, profile.longitude)
            ).km
            if distance > 100:
                continue
        else:
            distance = None

        # Random gallery image fallback
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

@login_required
def gallery_form(request):
    if request.method == "POST":
        images = request.FILES.getlist("images")
        for img in images:
            Gallery.objects.create(user=request.user, image=img)
        return redirect("home")  # after uploading, go to home or swipe page
    return render(request, "myapp/gallery_form.html")
