from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from myapp.models import Profile
from .models import Swipe
from django.http import JsonResponse

@login_required
def swipe_page(request):
    # Exclude profiles already swiped on or the user's own
    swiped_ids = Swipe.objects.filter(swiper=request.user).values_list('swiped_id', flat=True)
    profile = Profile.objects.exclude(user=request.user).exclude(id__in=swiped_ids).first()
    return render(request, 'swipes/swipes.html', {'profile': profile})

@login_required
def swipe_action(request):
    if request.method == 'POST':
        profile_id = request.POST.get('profile_id')
        action = request.POST.get('action')  # 'like' or 'dislike'
        profile = get_object_or_404(Profile, id=profile_id)

        Swipe.objects.update_or_create(
            swiper=request.user,
            swiped=profile,
            defaults={'action': action}
        )
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'}, status=400)
