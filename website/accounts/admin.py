from django.contrib import admin
from .models import Profile, Membership, SubscriptionEvent

# Register your models here.

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'location_country', 'timezone', 'language_preference', 'email_confirmed', 'subscription_status')
    list_filter = ('location_country', 'timezone', 'language_preference', 'email_confirmed', 'subscription_status')
    search_fields = ('user__username', 'user__email', 'location_country', 'timezone', 'language_preference')
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'bio', 'profile_image')
        }),
        ('Location & Preferences', {
            'fields': ('location_country', 'timezone', 'language_preference')
        }),
        ('Account Status', {
            'fields': ('email_confirmed', 'subscription_status')
        }),
        ('Security', {
            'fields': ('two_factor_enabled', 'two_factor_secret', 'recovery_codes'),
            'classes': ('collapse',)
        }),
        ('Stripe Integration', {
            'fields': ('stripe_customer_id', 'stripe_subscription_id'),
            'classes': ('collapse',)
        })
    )

admin.site.register(Membership)
admin.site.register(SubscriptionEvent)
