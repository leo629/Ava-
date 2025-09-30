from notifications.models import Notification
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import JsonResponse

from django.contrib.auth.models import AnonymousUser
from django.views.decorators.http import require_POST


@require_POST
@login_required
def mark_notifications_read(request):
    Notification.objects.filter(
        recipient=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'status': 'ok'})


def fetch_notifications(request):
    if isinstance(request.user, AnonymousUser) or not request.user.is_authenticated:
        return JsonResponse({'unread_count': 0, 'notifications': []})

    all_notifications = Notification.objects.filter(
        recipient=request.user).order_by('-timestamp')
    unread_count = all_notifications.filter(is_read=False).count()

    notifications = all_notifications[:10]

    data = {
        'unread_count': unread_count,
        'notifications': [
            {
                'id': n.id,
                'message': n.message,
                'type': n.notification_type,
                'timestamp': n.timestamp.isoformat(),
                'is_read': n.is_read
            }
            for n in notifications
        ]
    }
    return JsonResponse(data)


def send_notification(sender, recipient, notification_type, message=""):
    Notification.objects.create(
        sender=sender,
        recipient=recipient,
        notification_type=notification_type,
        message=message
    )


@login_required
def notification_list(request):
    notifications = Notification.objects.filter(
        recipient=request.user).order_by('-timestamp')
    return render(request, 'notifications/notification_list.html', {'notifications': notifications})
