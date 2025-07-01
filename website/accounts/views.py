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
from .models import Profile, Membership
from django.http import HttpResponse
from django.contrib import messages
import logging
from .forms import CustomUserCreationForm, ProfileImageForm
from django.conf import settings
import stripe
from django.views.decorators.csrf import csrf_exempt
from functools import wraps
from django.views.decorators.http import require_POST

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY

# Custom decorator for subscription-required pages
def subscription_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        # Check if user has an active subscription
        if hasattr(request.user, 'profile'):
            if request.user.profile.subscription_status == 'active':
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, 'This page requires an active subscription.')
                return redirect('subscribe')
        else:
            messages.error(request, 'Profile not found. Please contact support.')
            return redirect('home')
    
    return _wrapped_view

# Templates needed: accounts/register.html, accounts/profile.html, accounts/home.html, accounts/login.html, accounts/registration_pending.html
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = True  # User can log in, but we will check email_confirmed
            user.save()
            # profile = Profile.objects.create(user=user)
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
    profile = request.user.profile
    product_name = None
    current_period_end = None
    current_period_start = None
    if profile.stripe_subscription_id:
        try:
            subscription = stripe.Subscription.retrieve(profile.stripe_subscription_id)
            price = subscription['items']['data'][0]['price']
            product = stripe.Product.retrieve(price['product'])
            product_name = product['name']
            item = subscription['items']['data'][0]
            current_period_end = item.get('current_period_end')
            current_period_start = item.get('current_period_start')
        except Exception as e:
            product_name = None  # Optionally log the error
            current_period_end = None
            current_period_start = None
    return render(request, 'accounts/profile.html', {
        'profile': profile,
        'subscription_product_name': product_name,
        'current_period_end': current_period_end,
        'current_period_start': current_period_start,
    })


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
        return render(request, 'accounts/email_confirmed.html')
    else:
        return HttpResponse('Invalid confirmation link.')

def subscribe(request):
    memberships = Membership.objects.all()
    return render(request, "accounts/subscribe.html", {"memberships": memberships, "stripe_pk": settings.STRIPE_PUBLISHABLE_KEY})

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

def create_checkout_session(request, membership_id):
    if not request.user.is_authenticated:
        return redirect('login')
    
    membership = Membership.objects.get(id=membership_id)
    
    # Get or create Stripe customer
    if not request.user.profile.stripe_customer_id:
        customer = stripe.Customer.create(
            email=request.user.email,
            name=request.user.username,
        )
        request.user.profile.stripe_customer_id = customer.id
        request.user.profile.save()
    
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        mode='subscription',
        customer=request.user.profile.stripe_customer_id,
        line_items=[{
            'price': membership.stripe_price_id,
            'quantity': 1,
        }],
        success_url=request.build_absolute_uri('/accounts/success/'),
        cancel_url=request.build_absolute_uri('/accounts/cancel/'),
    )
    return redirect(session.url)

def subscription_success(request):
    return render(request, 'accounts/subscription_success.html')

def subscription_cancel(request):
    return render(request, 'accounts/subscription_cancel.html')

@csrf_exempt
def stripe_webhook(request):
    import stripe
    import logging
    logger = logging.getLogger(__name__)
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET
    event = None

    logger.info('Stripe webhook received!')
    logger.debug(f'Payload length: {len(payload)}')
    logger.debug(f'Signature header: {sig_header}')

    if not endpoint_secret:
        logger.error('STRIPE_WEBHOOK_SECRET not configured in settings')
        return HttpResponse(status=500)

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
        logger.info(f'Stripe event type: {event["type"]}')
    except ValueError as e:
        logger.error(f'Invalid payload: {e}')
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        logger.error(f'Invalid signature: {e}')
        return HttpResponse(status=400)

    if event['type'] in ['customer.subscription.created', 'customer.subscription.updated', 'customer.subscription.deleted']:
        subscription = event['data']['object']
        stripe_subscription_id = subscription['id']
        stripe_customer_id = subscription['customer']
        status = subscription['status']
        from .models import Profile
        try:
            profile = Profile.objects.get(stripe_customer_id=stripe_customer_id)
            profile.stripe_subscription_id = stripe_subscription_id
            profile.subscription_status = status
            profile.save()
            logger.info(f'Updated profile for customer {stripe_customer_id} with subscription {stripe_subscription_id} and status {status}')
        except Profile.DoesNotExist:
            logger.warning(f'Profile with customer_id {stripe_customer_id} does not exist')
    return HttpResponse(status=200)

@login_required
def logged_in_page(request):
    return render(request, 'accounts/logged_in_page.html')

@subscription_required
def subscribing_page(request):
    return render(request, 'accounts/subscribing_page.html')

@login_required
def cancel_subscription(request):
    """Cancel the user's subscription in Stripe and update local status"""
    if not request.user.profile.stripe_subscription_id:
        messages.error(request, 'No active subscription found to cancel.')
        return redirect('profile')
    
    try:
        # Cancel the subscription in Stripe
        subscription = stripe.Subscription.modify(
            request.user.profile.stripe_subscription_id,
            cancel_at_period_end=True
        )
        
        logger.info(f'Cancelled subscription {request.user.profile.stripe_subscription_id} for user {request.user.username}')
        
        # Update local subscription status
        request.user.profile.subscription_status = 'canceled'
        request.user.profile.save()
        
        messages.success(request, 'Your subscription has been cancelled successfully. You will continue to have access until the end of your current billing period.')
        
    except stripe.error.StripeError as e:
        logger.error(f'Error cancelling subscription: {e}')
        messages.error(request, f'Error cancelling subscription: {str(e)}')
    except Exception as e:
        logger.error(f'Unexpected error cancelling subscription: {e}')
        messages.error(request, 'An unexpected error occurred while cancelling your subscription.')
    
    return redirect('profile')

@login_required
def reactivate_subscription(request):
    """Reactivate a cancelled subscription"""
    if not request.user.profile.stripe_subscription_id:
        messages.error(request, 'No subscription found to reactivate.')
        return redirect('profile')
    
    try:
        # Reactivate the subscription in Stripe
        subscription = stripe.Subscription.modify(
            request.user.profile.stripe_subscription_id,
            cancel_at_period_end=False
        )
        
        logger.info(f'Reactivated subscription {request.user.profile.stripe_subscription_id} for user {request.user.username}')
        
        # Update local subscription status
        request.user.profile.subscription_status = 'active'
        request.user.profile.save()
        
        messages.success(request, 'Your subscription has been reactivated successfully.')
        
    except stripe.error.StripeError as e:
        logger.error(f'Error reactivating subscription: {e}')
        messages.error(request, f'Error reactivating subscription: {str(e)}')
    except Exception as e:
        logger.error(f'Unexpected error reactivating subscription: {e}')
        messages.error(request, 'An unexpected error occurred while reactivating your subscription.')
    
    return redirect('profile')

@login_required
def subscription_details(request):
    """Display detailed subscription information"""
    if not request.user.profile.stripe_subscription_id:
        messages.error(request, 'No subscription found.')
        return redirect('profile')
    
    try:
        # Get subscription details from Stripe
        subscription = stripe.Subscription.retrieve(request.user.profile.stripe_subscription_id)
        
        # Get customer details
        customer = stripe.Customer.retrieve(request.user.profile.stripe_customer_id)
        
        # Get current period dates from the first item
        current_period_start = None
        current_period_end = None
        if subscription['items']['data']:
            item = subscription['items']['data'][0]
            current_period_start = item.get('current_period_start')
            current_period_end = item.get('current_period_end')
        
        # Get upcoming invoice if subscription is active
        upcoming_invoice = None
        if subscription.status == 'active':
            try:
                upcoming_invoice = stripe.Invoice.upcoming(customer=request.user.profile.stripe_customer_id)
            except Exception:
                pass
        
        context = {
            'subscription': subscription,
            'customer': customer,
            'upcoming_invoice': upcoming_invoice,
            'current_period_start': current_period_start,
            'current_period_end': current_period_end,
        }
        
        return render(request, 'accounts/subscription_details.html', context)
        
    except stripe.error.StripeError as e:
        logger.error(f'Error retrieving subscription details: {e}')
        messages.error(request, f'Error retrieving subscription details: {str(e)}')
        return redirect('profile')
    except Exception as e:
        logger.error(f'Unexpected error retrieving subscription details: {e}')
        messages.error(request, 'An unexpected error occurred while retrieving subscription details.')
        return redirect('profile')

@login_required
def cancel_subscription_immediately(request):
    """Cancel the user's subscription immediately in Stripe"""
    if not request.user.profile.stripe_subscription_id:
        messages.error(request, 'No active subscription found to cancel.')
        return redirect('profile')
    
    try:
        # Cancel the subscription immediately in Stripe
        subscription = stripe.Subscription.delete(request.user.profile.stripe_subscription_id)
        
        logger.info(f'Immediately cancelled subscription {request.user.profile.stripe_subscription_id} for user {request.user.username}')
        
        # Update local subscription status
        request.user.profile.subscription_status = 'canceled'
        request.user.profile.save()
        
        messages.success(request, 'Your subscription has been cancelled immediately. You no longer have access to premium features.')
        
    except stripe.error.StripeError as e:
        logger.error(f'Error cancelling subscription immediately: {e}')
        messages.error(request, f'Error cancelling subscription: {str(e)}')
    except Exception as e:
        logger.error(f'Unexpected error cancelling subscription immediately: {e}')
        messages.error(request, 'An unexpected error occurred while cancelling your subscription.')
    
    return redirect('profile')

@login_required
@require_POST
def delete_user(request):
    email_input = request.POST.get('email')
    if email_input and email_input.strip().lower() == request.user.email.strip().lower():
        user = request.user
        logout(request)
        user.delete()
        messages.success(request, 'Your account has been deleted.')
        return redirect('home')
    else:
        messages.error(request, 'The email address you entered does not match your account. Account not deleted.')
        return redirect('subscription_details')

@login_required
def upload_profile_image(request):
    if request.method == 'POST':
        form = ProfileImageForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile image updated successfully.')
        else:
            messages.error(request, 'There was an error uploading the image.')
    return redirect('profile')

@login_required
def clear_profile_image(request):
    if request.method == 'POST':
        profile = request.user.profile
        if profile.profile_image:
            profile.profile_image.delete(save=False)
            profile.profile_image = None
            profile.save()
            messages.success(request, 'Profile image removed.')
        else:
            messages.info(request, 'No profile image to remove.')
    return redirect('profile')

@login_required
def username_edit_htmx(request):
    user = request.user
    return render(request, 'accounts/partials/username_edit.html', {'user': user})

@login_required
@require_POST
def username_update_htmx(request):
    new_username = request.POST.get('username', '').strip()
    user = request.user
    error = None
    if not new_username:
        error = 'Username cannot be empty.'
    elif User.objects.filter(username=new_username).exclude(pk=user.pk).exists():
        error = 'This username is already taken.'
    elif len(new_username) < 3:
        error = 'Username must be at least 3 characters.'
    # Add more validation as needed
    if error:
        return render(request, 'accounts/partials/username_edit.html', {
            'user': user,
            'error': error,
        })
    user.username = new_username
    user.save()
    return render(request, 'accounts/partials/username_display.html', {'user': user})

@login_required
def bio_edit_htmx(request):
    user = request.user
    profile = user.profile
    return render(request, 'accounts/partials/bio_edit.html', {'profile': profile})

@login_required
@require_POST
def bio_update_htmx(request):
    new_bio = request.POST.get('bio', '').strip()
    user = request.user
    profile = user.profile
    error = None
    if len(new_bio) > 2000:
        error = 'Bio must be 2000 characters or less.'
    if error:
        return render(request, 'accounts/partials/bio_edit.html', {
            'profile': profile,
            'error': error,
            'bio': new_bio,
        })
    profile.bio = new_bio
    profile.save()
    return render(request, 'accounts/partials/bio_display.html', {'profile': profile})
