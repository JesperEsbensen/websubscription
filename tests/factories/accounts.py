"""Factory classes for accounts app models."""

import factory
from django.contrib.auth import get_user_model
from accounts.models import Profile, Membership, SubscriptionEvent
from faker import Faker

User = get_user_model()
fake = Faker()

class UserFactory(factory.django.DjangoModelFactory):
    """Factory for User model."""
    class Meta:
        model = User
    
    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    is_active = True
    is_staff = False
    is_superuser = False
    
    @factory.post_generation
    def password(obj, create, extracted, **kwargs):
        if create:
            password = extracted or 'testpass123'
            obj.set_password(password)
            obj.save()

class ProfileFactory(factory.django.DjangoModelFactory):
    """Factory for Profile model."""
    class Meta:
        model = Profile
    
    user = factory.SubFactory(UserFactory)
    bio = factory.Faker('text', max_nb_chars=500)
    email_confirmed = False
    stripe_customer_id = factory.Sequence(lambda n: f"cus_test{n}")
    stripe_subscription_id = factory.Sequence(lambda n: f"sub_test{n}")
    subscription_status = 'active'
    location_country = factory.Faker('country')
    timezone = 'UTC'
    language_preference = 'en'
    two_factor_enabled = False

class MembershipFactory(factory.django.DjangoModelFactory):
    """Factory for Membership model."""
    class Meta:
        model = Membership
    
    name = factory.Faker('word')
    stripe_price_id = factory.Sequence(lambda n: f"price_test{n}")
    description = factory.Faker('text', max_nb_chars=200)

class SubscriptionEventFactory(factory.django.DjangoModelFactory):
    """Factory for SubscriptionEvent model."""
    class Meta:
        model = SubscriptionEvent
    
    event_id = factory.Sequence(lambda n: f"evt_test{n}")
    event_type = factory.Faker('random_element', elements=[
        'customer.subscription.created',
        'customer.subscription.updated',
        'customer.subscription.deleted',
        'invoice.payment_succeeded'
    ])
    created = factory.Faker('date_time')
    data = factory.Dict({'test': 'data'})
    customer_id = factory.Sequence(lambda n: f"cus_test{n}")
    subscription_id = factory.Sequence(lambda n: f"sub_test{n}")