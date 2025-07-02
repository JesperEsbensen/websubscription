from django.urls import path
from . import views

urlpatterns = [
    path('subscribe/', views.subscribe, name='subscribe'),
    path('create-checkout-session/<int:membership_id>/', views.create_checkout_session, name='create_checkout_session'),
    path('success/', views.subscription_success, name='subscription_success'),
    path('cancel/', views.subscription_cancel, name='subscription_cancel'),
    path('stripe/webhook/', views.stripe_webhook, name='stripe_webhook'),
    path('cancel-subscription/', views.cancel_subscription, name='cancel_subscription'),
    path('cancel-subscription-immediately/', views.cancel_subscription_immediately, name='cancel_subscription_immediately'),
    path('reactivate-subscription/', views.reactivate_subscription, name='reactivate_subscription'),
    path('subscription-details/', views.subscription_details, name='subscription_details'),
    path('delete-user/', views.delete_user, name='delete_user'),
    path('upload-profile-image/', views.upload_profile_image, name='upload_profile_image'),
    path('clear-profile-image/', views.clear_profile_image, name='clear_profile_image'),
    path('username-edit-htmx/', views.username_edit_htmx, name='username_edit_htmx'),
    path('username-update-htmx/', views.username_update_htmx, name='username_update_htmx'),
    path('bio-edit-htmx/', views.bio_edit_htmx, name='bio_edit_htmx'),
    path('bio-update-htmx/', views.bio_update_htmx, name='bio_update_htmx'),
    path('resend-verification/', views.resend_verification_email, name='resend_verification_email'),
    path('enable-2fa/', views.enable_2fa, name='enable_2fa'),
    path('disable-2fa/', views.disable_2fa, name='disable_2fa'),
    path('show-recovery-codes/', views.show_recovery_codes, name='show_recovery_codes'),
    path('2fa-challenge/', views.two_factor_challenge, name='two_factor_challenge'),
] 