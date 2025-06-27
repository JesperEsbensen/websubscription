from django import template
from django.utils import timezone
from datetime import datetime

register = template.Library()

@register.filter
def stripe_timestamp_to_date(timestamp):
    """Convert Stripe timestamp to Django date format"""
    if timestamp:
        # Stripe timestamps are in Unix timestamp format
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%b %d, %Y")
    return ""

@register.filter
def stripe_amount_to_dollars(amount):
    """Convert Stripe amount (in cents) to dollars"""
    if amount:
        return f"${amount / 100:.2f}"
    return "$0.00" 