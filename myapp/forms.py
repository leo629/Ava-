from allauth.account.forms import SignupForm
from django import forms
from .models import Profile, Gallery
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget
from django.forms.widgets import DateInput


# Basic profile form for limited updates
class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio', 'gender', 'country', 'profile_pic']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 2}),
            'country': CountrySelectWidget(),
        }


# Full profile edit form with all fields
class EditProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
            'bio',
            'gender',
            'country',
            'profile_pic',
            'interests',
            'hobbies',
            'want_kids',
            'relationship_goal',
            'lifestyle',
            'date_of_birth',
        ]
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3}),
            'interests': forms.Textarea(attrs={'rows': 2}),
            'hobbies': forms.Textarea(attrs={'rows': 2}),
            'country': CountrySelectWidget(),
            'date_of_birth': DateInput(attrs={'type': 'date'}),
        }


# Gallery upload form
class GalleryForm(forms.ModelForm):
    class Meta:
        model = Gallery
        fields = ['image', 'caption']
        widgets = {
            'caption': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Add a caption (optional)'})
        }


# Custom signup form to collect profile info on registration
class CustomSignupForm(SignupForm):
    bio = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)
    gender = forms.ChoiceField(choices=Profile.GENDER_CHOICES, required=False)
    profile_pic = forms.ImageField(required=False)
    country = CountryField(blank=True).formfield(widget=CountrySelectWidget())

    phone_number = forms.CharField(max_length=15, required=True, label="Phone Number")
    date_of_birth = forms.DateField(
        label="Date of Birth",
        required=True,
        widget=DateInput(attrs={'type': 'date'})
    )

    interests = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}), required=False)
    hobbies = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}), required=False)
    want_kids = forms.ChoiceField(choices=Profile.WANT_KIDS_CHOICES, required=False)
    relationship_goal = forms.ChoiceField(choices=Profile.RELATIONSHIP_GOALS, required=False)
    lifestyle = forms.ChoiceField(choices=Profile.LIFESTYLE_CHOICES, required=False)

    def save(self, request):
        user = super().save(request)

        # Save extra profile fields
        profile = user.profile
        profile.bio = self.cleaned_data.get('bio')
        profile.gender = self.cleaned_data.get('gender')
        profile.country = self.cleaned_data.get('country')
        profile.profile_pic = self.cleaned_data.get('profile_pic')
        profile.date_of_birth = self.cleaned_data.get('date_of_birth')
        profile.interests = self.cleaned_data.get('interests')
        profile.hobbies = self.cleaned_data.get('hobbies')
        profile.want_kids = self.cleaned_data.get('want_kids')
        profile.relationship_goal = self.cleaned_data.get('relationship_goal')
        profile.lifestyle = self.cleaned_data.get('lifestyle')
        profile.save()

        user.phone_number = self.cleaned_data.get("phone_number")
        user.save()

        return user
