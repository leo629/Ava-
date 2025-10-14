

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.http import JsonResponse
from myapp.models import Profile, Like, Gallery  # adjust imports as needed
from .models import Swipe
from django.contrib.auth.models import User

# ---------------------------
# SWIPE PAGE VIEW
# ---------------------------
@login_required
def swipe_page(request):
    viewer_profile = request.user.profile

    # ✅ Show only opposite gender profiles
    opposite_gender = "female" if viewer_profile.gender == "male" else "male"

    # ✅ Exclude already swiped or current user
    swiped_ids = Swipe.objects.filter(swiper=request.user).values_list('swiped_id', flat=True)

    # ✅ Get first available profile
    profile = (
        Profile.objects.filter(gender=opposite_gender)
        .exclude(user=request.user)
        .exclude(id__in=swiped_ids)
        .order_by("?")
        .first()
    )

    return render(request, 'swipes/swipes.html', {'profile': profile})


# ---------------------------
# SWIPE ACTION VIEW
# ---------------------------
@login_required
def swipe_action(request):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)

    profile_id = request.POST.get("profile_id")
    action = request.POST.get("action")

    if not profile_id or action not in ["like", "dislike"]:
        return JsonResponse({"status": "error", "message": "Invalid data"}, status=400)

    # Get the Profile being swiped
    swiped_profile = get_object_or_404(Profile, id=profile_id)
    swiper_profile = request.user.profile

    # Record the swipe
    swipe, created = Swipe.objects.get_or_create(
        swiper=request.user,  # keep User for compatibility
        swiped=swiped_profile,
        defaults={'action': action}
    )

    if not created:
        swipe.action = action
        swipe.save()

    # ✅ Check for a MATCH (both users liked each other)
    if action == "like":
        liked_back = Swipe.objects.filter(
            swiper=swiped_profile.user,
            swiped=swiper_profile,
            action="like"
        ).exists()

        if liked_back:
            # Optional: create a Match model or send notification
            print("🎉 It's a match between", swiper_profile.user.username, "and", swiped_profile.user.username)

    # ✅ Get next profile (opposite gender + not swiped yet)
    opposite_gender = "female" if swiper_profile.gender == "male" else "male"

    swiped_ids = Swipe.objects.filter(swiper=request.user).values_list('swiped_id', flat=True)
    next_profile = (
        Profile.objects.filter(gender=opposite_gender)
        .exclude(user=request.user)
        .exclude(id__in=swiped_ids)
        .order_by("?")
        .first()
    )

    if not next_profile:
        return JsonResponse({"status": "ok", "next_profile": None})

    # ✅ Prepare gallery images safely
    images = []
    if next_profile.profile_pic:
        images.append(next_profile.profile_pic.url)

    gallery_images = getattr(next_profile, 'gallery_set', None)
    if gallery_images:
        images += [img.image.url for img in gallery_images.all()]

    return JsonResponse({
        "status": "ok",
        "next_profile": {
            "id": next_profile.id,
            "username": next_profile.user.username,
            "bio": next_profile.bio or "",
            "images": images or ["/static/images/default_profile.jpg"],
        }
    })
    
