from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # Django AllAuth authentication URLs
    path('accounts/', include('allauth.urls')),
    path('chat/', include('chat.urls')),  # Chat app URLs
    path('', include('myapp.urls')),  # Main app URLs
    path('notifications/', include('notifications.urls')),
    path('swipes/', include('swipes.urls')),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
