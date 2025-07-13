from django.db import models
from django.contrib.auth.models import User
from django_countries.fields import CountryField
from datetime import date
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.timesince import timesince


class Profile(models.Model):
    GENDER_CHOICES = [('M', 'Male'), ('F', 'Female'), ('O', 'Other')]
    WANT_KIDS_CHOICES = [('yes', 'Yes'), ('no', 'No'), ('maybe', 'Maybe')]
    RELATIONSHIP_GOALS = [('casual', 'Casual'), ('serious', 'Serious'), ('marriage', 'Marriage')]
    LIFESTYLE_CHOICES = [('active', 'Active'), ('chill', 'Chill'), ('party', 'Party Animal'), ('homebody', 'Homebody')]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    profile_pic = models.ImageField(upload_to='profile_pics/', blank=True, null=True, default='gallery_images/default.jpg')
    country = CountryField(blank=True, null=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    city = models.CharField(max_length=255, blank=True)
    interests = models.TextField(blank=True)
    hobbies = models.TextField(blank=True)
    want_kids = models.CharField(max_length=10, choices=WANT_KIDS_CHOICES, blank=True)
    relationship_goal = models.CharField(max_length=10, choices=RELATIONSHIP_GOALS, blank=True)
    lifestyle = models.CharField(max_length=10, choices=LIFESTYLE_CHOICES, blank=True)
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username}'s profile"

    @property
    def age(self):
        if self.date_of_birth:
            today = date.today()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None

    def get_last_seen_display(self):
        return timesince(self.last_seen) + " ago"


class Like(models.Model):
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes_sent')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes_received')
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('from_user', 'to_user')

    def __str__(self):
        return f"{self.from_user.username} liked {self.to_user.username}"


class Match(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='initiated_matches')
    target = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_matches')
    liked = models.BooleanField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'target')


class Gallery(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='gallery_images/')
    caption = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s gallery image"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
