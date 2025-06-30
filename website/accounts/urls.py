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
] 