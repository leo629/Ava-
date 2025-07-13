
from django.db import models
from django.contrib.auth.models import User
from myapp.models import Profile  # assuming you have this

class Swipe(models.Model):
    SWIPE_CHOICES = (
        ('like', 'Like'),
        ('dislike', 'Dislike'),
    )

    swiper = models.ForeignKey(User, on_delete=models.CASCADE, related_name='swipes_made')
    swiped = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='swipes_received')
    action = models.CharField(max_length=10, choices=SWIPE_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('swiper', 'swiped')  # prevent duplicate swipes
