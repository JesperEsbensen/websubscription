from django import template
import json
from django.apps import apps

register = template.Library()

EVENT_NAME_MAP = {
    'customer.subscription.created': 'Subscription Created',
    'customer.subscription.deleted': 'Subscription Cancelled',
    'customer.subscription.updated': 'Subscription Updated',
    'invoice.created': 'Invoice Created',
    'invoice.deleted': 'Invoice Deleted',
    'invoice.finalization_failed': 'Invoice Finalization Failed',
    'invoice.finalized': 'Invoice Finalized',
    'invoice.marked_uncollectible': 'Invoice Marked Uncollectible',
    'invoice.overdue': 'Invoice Overdue',
    'invoice.overpaid': 'Invoice Overpaid',
    'invoice.paid': 'Invoice Paid',
    'invoice.payment_action_required': 'Invoice Payment Action Required',
    'invoice.payment_failed': 'Invoice Payment Failed',
    'invoice.payment_succeeded': 'Invoice Payment Succeeded',
    'invoice.sent': 'Invoice Sent',
    'invoice.upcoming': 'Invoice Upcoming',
    'invoice.updated': 'Invoice Updated',
    'invoice.voided': 'Invoice Voided',
    'invoice.will_be_due': 'Invoice Will Be Due',
    'invoice_payment.paid': 'Invoice Payment Paid',
}

@register.filter
def event_friendly_name(event_type):
    return EVENT_NAME_MAP.get(event_type, event_type)

@register.filter
def startswith(text, starts):
    if isinstance(text, str):
        return text.startswith(starts)
    return False

@register.filter
def event_friendly_name_with_cancel_check(event):
    event_type = getattr(event, 'event_type', None)
    data = getattr(event, 'data', None)
    if event_type == 'customer.subscription.updated' and data:
        obj = data.get('object') if isinstance(data, dict) else None
        prev = data.get('previous_attributes') if isinstance(data, dict) else None
        if obj and obj.get('cancel_at_period_end'):
            return 'Subscription Cancelled at End of Period'
        if obj and prev and obj.get('cancel_at_period_end') is False and prev.get('cancel_at_period_end') is True:
            return 'Subscription Reactivated'
    return event_friendly_name(event_type)

@register.filter
def event_invoice_amount(event):
    data = getattr(event, 'data', None)
    if not data or not isinstance(data, dict):
        return ""
    obj = data.get('object')
    if not obj:
        return ""
    # Use amount_paid if available, else amount_due
    amount = obj.get('amount_paid') or obj.get('amount_due')
    if amount is not None:
        currency = obj.get('currency', '').upper()
        return f"{amount / 100:.2f} {currency}"
    return ""

@register.filter
def event_subscription_product_name(event):
    data = getattr(event, 'data', None)
    if not data or not isinstance(data, dict):
        return ""
    obj = data.get('object')
    if not obj:
        return ""
    # Try to get the price id from the first item
    items = obj.get('items', {}).get('data', [])
    if items:
        price = items[0].get('price')
        price_id = None
        if price:
            if isinstance(price, dict):
                price_id = price.get('id')
            elif isinstance(price, str):
                price_id = price
        if price_id:
            Membership = apps.get_model('accounts', 'Membership')
            membership = Membership.objects.filter(stripe_price_id=price_id).first()
            if membership:
                return membership.name
        # Fallback to price nickname or id
        if price and isinstance(price, dict):
            return price.get('nickname') or price.get('id')
    return "" 