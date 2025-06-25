from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from .models import Profile
from django.http import HttpResponse
from django.contrib import messages
import logging
from .forms import CustomUserCreationForm

logger = logging.getLogger(__name__)

# Templates needed: accounts/register.html, accounts/profile.html, accounts/home.html, accounts/login.html, accounts/registration_pending.html
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = True  # User can log in, but we will check email_confirmed
            user.save()
            profile = Profile.objects.create(user=user)
            # Send confirmation email
            current_site = get_current_site(request)
            subject = 'Confirm your email'
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            confirm_url = f"http://{current_site.domain}/confirm-email/{uid}/{token}/"
            message = render_to_string('accounts/confirm_email.html', {
                'user': user,
                'confirm_url': confirm_url,
            })
            try:
                send_mail(subject, message, None, [user.email])
                logger.info(f"Confirmation email sent to {user.email}")
            except Exception as e:
                logger.error(f"Failed to send confirmation email to {user.email}: {e}")
            return render(request, 'accounts/registration_pending.html', {'email': user.email})
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})


def custom_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                if hasattr(user, 'profile') and not user.profile.email_confirmed:
                    messages.error(request, 'Please confirm your email before logging in.')
                    return render(request, 'accounts/login.html', {'form': form})
                login(request, user)
                return redirect('profile')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})


@login_required
def profile(request):
    return render(request, 'accounts/profile.html', {'profile': request.user.profile})


def home(request):
    return render(request, 'accounts/home.html')


def confirm_email(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and default_token_generator.check_token(user, token):
        user.profile.email_confirmed = True
        user.profile.save()
        return HttpResponse('Email confirmed! You can now log in.')
    else:
        return HttpResponse('Invalid confirmation link.')
