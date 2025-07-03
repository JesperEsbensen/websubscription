from django import template
import json

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