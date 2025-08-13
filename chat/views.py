from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Message
from django.contrib.auth.models import User
from django.db.models import Q, Count
from django.http import JsonResponse


@login_required
def unread_messages(request):
    unread_count = Message.objects.filter(
        receiver=request.user, is_read=False).count()
    return JsonResponse({"unread_count": unread_count})


@login_required
def chat_list(request):
    sent = Message.objects.filter(
        sender=request.user).values_list('receiver', flat=True)
    received = Message.objects.filter(
        receiver=request.user).values_list('sender', flat=True)
    user_ids = set(sent).union(set(received))

    chat_users = []

    for uid in user_ids:
        if uid == request.user.id:
            continue

        user = User.objects.get(id=uid)

        # Get the last message
        last_message = Message.objects.filter(
            Q(sender=request.user, receiver=user) |
            Q(sender=user, receiver=request.user)
        ).order_by('-timestamp').first()

        # Count unread messages from this user to the current user
        unread_count = Message.objects.filter(
            sender=user,
            receiver=request.user,
            is_read=False
        ).count()

        chat_users.append({
            'user': user,
            'last_message': last_message,
            'unread_count': unread_count,
        })

    # Sort by timestamp of last message (latest first)
    chat_users.sort(
        key=lambda x: x['last_message'].timestamp if x['last_message'] else None, reverse=True)

    return render(request, 'chat/chat_list.html', {'chat_users': chat_users})


@login_required
def chat_room(request, username):
    other_user = get_object_or_404(User, username=username)

    if not hasattr(other_user, 'profile'):
        Profile.objects.create(user=other_user)

    messages = Message.objects.filter(
        sender=request.user, receiver=other_user
    ) | Message.objects.filter(
        sender=other_user, receiver=request.user
    )

    messages = messages.order_by("timestamp")  # Sorting messages by time

    context = {
        "other_user": other_user,
        "is_online": other_user.profile.is_online,
        "last_seen": other_user.profile.last_seen,
        "messages": messages,
    }
    return render(request, "chat/chat.html", context)


def home(request):
    # Get all registered users except the logged-in user
    # Exclude the logged-in user
    users = User.objects.exclude(id=request.user.id)
    return render(request, 'myapp/home.html', {'users': users})


def message_detail(request, user_id):
    sender = get_object_or_404(User, id=user_id)
    messages = Message.objects.filter(
        sender=sender,
        recipient=request.user
    )
    messages.update(is_read=True)  # mark as read
    return render(request, 'chat/message_detail.html', {'messages': messages, 'sender': sender})
