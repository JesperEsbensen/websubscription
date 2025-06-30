from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

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