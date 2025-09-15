from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import Profile


class Command(BaseCommand):
    help = 'Update user profile with location and preferences'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username to update')
        parser.add_argument('--country', type=str, help='Country name')
        parser.add_argument('--timezone', type=str, help='Timezone (e.g., Europe/Copenhagen)')
        parser.add_argument('--language', type=str, help='Language code (e.g., en, da)')

    def handle(self, *args, **options):
        username = options['username']
        
        try:
            user = User.objects.get(username=username)
            profile = user.profile
            
            updated_fields = []
            
            if options['country']:
                profile.location_country = options['country']
                updated_fields.append(f"country: {options['country']}")
            
            if options['timezone']:
                profile.timezone = options['timezone']
                updated_fields.append(f"timezone: {options['timezone']}")
            
            if options['language']:
                profile.language_preference = options['language']
                updated_fields.append(f"language: {options['language']}")
            
            if updated_fields:
                profile.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully updated profile for {username}: {", ".join(updated_fields)}'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING('No fields to update. Use --country, --timezone, or --language options.')
                )
                
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User "{username}" does not exist.')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error updating profile: {e}')
            )
