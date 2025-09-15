from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
import pytz

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user

class ProfileImageForm(forms.ModelForm):
    class Meta:
        from .models import Profile
        model = Profile
        fields = ['profile_image']

    def clean_profile_image(self):
        image = self.cleaned_data.get('profile_image')
        if image:
            ext = image.name.split('.')[-1].lower()
            if ext not in ['jpg', 'jpeg', 'png']:
                raise forms.ValidationError('Only .jpg and .png files are allowed.')
        return image


class ProfileUpdateForm(forms.ModelForm):
    """Form for updating user profile information including location and preferences"""
    
    # Common countries for the dropdown
    COUNTRY_CHOICES = [
        ('', 'Select a country...'),
        ('Denmark', 'Denmark'),
        ('Sweden', 'Sweden'),
        ('Norway', 'Norway'),
        ('Finland', 'Finland'),
        ('Germany', 'Germany'),
        ('Netherlands', 'Netherlands'),
        ('United Kingdom', 'United Kingdom'),
        ('United States', 'United States'),
        ('Canada', 'Canada'),
        ('Australia', 'Australia'),
        ('France', 'France'),
        ('Spain', 'Spain'),
        ('Italy', 'Italy'),
        ('Other', 'Other'),
    ]
    
    # Common timezones
    TIMEZONE_CHOICES = [
        ('', 'Select a timezone...'),
        ('Europe/Copenhagen', 'Europe/Copenhagen (Denmark)'),
        ('Europe/Stockholm', 'Europe/Stockholm (Sweden)'),
        ('Europe/Oslo', 'Europe/Oslo (Norway)'),
        ('Europe/Helsinki', 'Europe/Helsinki (Finland)'),
        ('Europe/Berlin', 'Europe/Berlin (Germany)'),
        ('Europe/Amsterdam', 'Europe/Amsterdam (Netherlands)'),
        ('Europe/London', 'Europe/London (UK)'),
        ('America/New_York', 'America/New_York (US East)'),
        ('America/Los_Angeles', 'America/Los_Angeles (US West)'),
        ('America/Toronto', 'America/Toronto (Canada)'),
        ('Australia/Sydney', 'Australia/Sydney'),
        ('UTC', 'UTC (Coordinated Universal Time)'),
    ]
    
    # Language choices
    LANGUAGE_CHOICES = [
        ('', 'Select a language...'),
        ('en', 'English'),
        ('da', 'Danish'),
        ('sv', 'Swedish'),
        ('no', 'Norwegian'),
        ('fi', 'Finnish'),
        ('de', 'German'),
        ('nl', 'Dutch'),
        ('fr', 'French'),
        ('es', 'Spanish'),
        ('it', 'Italian'),
    ]
    
    location_country = forms.ChoiceField(
        choices=COUNTRY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    timezone = forms.ChoiceField(
        choices=TIMEZONE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    language_preference = forms.ChoiceField(
        choices=LANGUAGE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        from .models import Profile
        model = Profile
        fields = ['bio', 'location_country', 'timezone', 'language_preference']
        widgets = {
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Tell us about yourself...'
            }),
        }
    
    def clean_timezone(self):
        timezone = self.cleaned_data.get('timezone')
        if timezone and timezone not in [tz[0] for tz in self.TIMEZONE_CHOICES]:
            raise forms.ValidationError('Please select a valid timezone.')
        return timezone
    
    def clean_language_preference(self):
        language = self.cleaned_data.get('language_preference')
        if language and language not in [lang[0] for lang in self.LANGUAGE_CHOICES]:
            raise forms.ValidationError('Please select a valid language.')
        return language 