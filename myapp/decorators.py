from django.shortcuts import redirect
from .models import Gallery


def require_gallery(min_images=4):
    """
    Redirect users to gallery upload if they haven't uploaded
    the minimum number of images.
    """
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_authenticated:
                gallery_count = Gallery.objects.filter(
                    user=request.user).count()
                if gallery_count < min_images:
                    return redirect('upload_gallery')
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
