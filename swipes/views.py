from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.http import JsonResponse
from django.db.models import F
from myapp.models import Profile, Gallery
from .models import Swipe
from math import radians, sin, cos, sqrt, atan2


# -------------------------------
# Distance calculation
# -------------------------------
def calculate_distance(lat1, lon1, lat2, lon2):
    if None in [lat1, lon1, lat2, lon2]:
        return None  # Cannot calculate
    
    R = 6371  # KM
    d_lat = radians(lat2 - lat1)
    d_lon = radians(lon2 - lon1)

    a = sin(d_lat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return round(R * c, 1)


# -------------------------------
# Swipe Page
# -------------------------------
@login_required
def swipe_page(request):
    profile = request.user.profile

    # Save GPS if browser sent it
    lat = request.GET.get("lat")
    lon = request.GET.get("lon")
    if lat and lon:
        profile.latitude = lat
        profile.longitude = lon
        profile.save()

    opposite_gender = "female" if profile.gender == "male" else "male"

    swiped_ids = Swipe.objects.filter(swiper=request.user).values_list("swiped_id", flat=True)

    queryset = Profile.objects.filter(
        gender=opposite_gender
    ).exclude(user=request.user).exclude(id__in=swiped_ids)

    # Add distance sorting
    profiles_with_distance = []
    for p in queryset:
        dist = calculate_distance(profile.latitude, profile.longitude, p.latitude, p.longitude)
        profiles_with_distance.append((p, dist))

    # Sort by distance first
    profiles_with_distance.sort(key=lambda x: (x[1] is None, x[1]))

    next_profile = profiles_with_distance[0][0] if profiles_with_distance else None

    return render(request, "swipes/swipes.html", {"profile": next_profile})


# -------------------------------
# Swipe Action
# -------------------------------
@login_required
def swipe_action(request):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)

    profile_id = request.POST.get("profile_id")
    action = request.POST.get("action")

    if not profile_id or action not in ["like", "dislike", "superlike"]:
        return JsonResponse({"status": "error", "message": "Invalid data"}, status=400)

    swiped_profile = get_object_or_404(Profile, id=profile_id)
    viewer_profile = request.user.profile

    # Save swipe
    swipe, created = Swipe.objects.get_or_create(
        swiper=request.user,
        swiped=swiped_profile,
        defaults={'action': action}
    )

    if not created:
        swipe.action = action
        swipe.save()

    # Check match only on LIKE / SUPERLIKE
    is_match = False
    if action in ["like", "superlike"]:
        liked_back = Swipe.objects.filter(
            swiper=swiped_profile.user,
            swiped=viewer_profile,
            action__in=["like", "superlike"]
        ).exists()
        if liked_back:
            is_match = True

    # ------------------------------------
    # Get next profile
    # ------------------------------------
    opposite_gender = "female" if viewer_profile.gender == "male" else "male"
    swiped_ids = Swipe.objects.filter(swiper=request.user).values_list("swiped_id", flat=True)
    queryset = Profile.objects.filter(gender=opposite_gender).exclude(user=request.user).exclude(id__in=swiped_ids)

    profiles_with_distance = []
    for p in queryset:
        dist = calculate_distance(viewer_profile.latitude, viewer_profile.longitude, p.latitude, p.longitude)
        profiles_with_distance.append((p, dist))

    profiles_with_distance.sort(key=lambda x: (x[1] is None, x[1]))

    if not profiles_with_distance:
        return JsonResponse({"status": "ok", "next_profile": None, "match": is_match})

    next_profile = profiles_with_distance[0][0]
    distance = profiles_with_distance[0][1]

    # Collect images (profile + gallery)
    images = []
    if next_profile.profile_pic:
        images.append(next_profile.profile_pic.url)
    gallery_images = Gallery.objects.filter(user=next_profile.user)
    images += [g.image.url for g in gallery_images]

    if not images:
        images = ["/static/images/default_profile.jpg"]

    return JsonResponse({
        "status": "ok",
        "match": is_match,
        "next_profile": {
            "id": next_profile.id,
            "username": next_profile.user.username,
            "bio": next_profile.bio or "",
            "distance": distance,
            "images": images,
        }
    })

