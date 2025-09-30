from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.http import JsonResponse
from myapp.models import Profile
from .models import Swipe
from itertools import chain


@login_required
def swipe_page(request):
    # Exclude profiles already swiped or the current user
    swiped_ids = Swipe.objects.filter(
        swiper=request.user).values_list('swiped_id', flat=True)
    profile = Profile.objects.exclude(user=request.user).exclude(
        user__id__in=swiped_ids).first()
    return render(request, 'swipes/swipes.html', {'profile': profile})


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

    # ✅ Use Profile objects instead of User
    swiper_profile = request.user.profile

    swipe, created = Swipe.objects.get_or_create(
        swiper=request.user,        # ✅ User
        swiped=swiped_profile,      # ✅ Profile
        defaults={'action': action}
    )

    if not created:
        swipe.action = action
        swipe.save()

    # Get next profile excluding already swiped
    swiped_ids = Swipe.objects.filter(
        swiper=request.user    # ✅ User
    ).values_list('swiped_id', flat=True)

    next_profile = Profile.objects.exclude(user=request.user).exclude(
        id__in=swiped_ids
    ).order_by("?").first()

    if not next_profile:
        return JsonResponse({"status": "ok", "next_profile": None})

    # Prepare gallery images
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
            "images": images,
        }
    })
