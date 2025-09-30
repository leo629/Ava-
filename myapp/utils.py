# utils.py
import random
from geopy.distance import geodesic
from .models import Gallery


def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate distance in km between two coordinates.
    """
    try:
        return geodesic((lat1, lon1), (lat2, lon2)).km
    except Exception:
        return None


def filter_potential_matches(user_profile, candidates, max_age_diff=5, max_distance=100):
    """
    Filters potential matches by age difference and distance.
    Returns a list of dicts with match info.
    """
    matches = []

    for profile in candidates:
        # ✅ Age filter
        if profile.age and user_profile.age:
            if abs(profile.age - user_profile.age) > max_age_diff:
                continue

        # ✅ Distance filter
        if all([profile.latitude, profile.longitude, user_profile.latitude, user_profile.longitude]):
            distance = geodesic(
                (user_profile.latitude, user_profile.longitude),
                (profile.latitude, profile.longitude)
            ).km
            if distance > max_distance:
                continue
        else:
            distance = None

        # ✅ Pick random gallery image or fallback
        gallery_images = Gallery.objects.filter(user=profile.user)
        if gallery_images.exists():
            image_url = random.choice(list(gallery_images)).image.url
        elif profile.profile_pic and hasattr(profile.profile_pic, "url"):
            image_url = profile.profile_pic.url
        else:
            image_url = '/static/img/default.jpg'

        matches.append({
            'username': profile.user.username,
            'age': profile.age,
            'city': profile.city or "Unknown",
            'image': image_url,
            'distance': round(distance, 1) if distance else "Unknown"
        })

    return matches
