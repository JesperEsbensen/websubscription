from django.core.management.base import BaseCommand
from chatbot.models import FormQuestion


class Command(BaseCommand):
    help = 'Create sample form questions for testing'

    def handle(self, *args, **options):
        # Sample ESG Assessment Form
        esg_form, created = FormQuestion.objects.get_or_create(
            title="ESG Assessment Form",
            defaults={
                'description': 'Please provide information about your company\'s ESG practices and goals.',
                'field_type': 'textarea',
                'field_name': 'esg_assessment',
                'field_label': 'Describe your current ESG initiatives and goals',
                'placeholder': 'Please describe your company\'s environmental, social, and governance practices, including any specific goals or challenges you\'re facing...',
                'required': True,
                'order': 1,
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('Created ESG Assessment Form'))
        else:
            self.stdout.write(self.style.WARNING('ESG Assessment Form already exists'))

        # Company Information Form
        company_form, created = FormQuestion.objects.get_or_create(
            title="Company Information",
            defaults={
                'description': 'Basic information about your company for better support.',
                'field_type': 'text',
                'field_name': 'company_name',
                'field_label': 'Company Name',
                'placeholder': 'Enter your company name',
                'required': True,
                'order': 2,
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('Created Company Information Form'))
        else:
            self.stdout.write(self.style.WARNING('Company Information Form already exists'))

        # Industry Selection Form
        industry_form, created = FormQuestion.objects.get_or_create(
            title="Industry Selection",
            defaults={
                'description': 'Please select your industry to receive more relevant ESG guidance.',
                'field_type': 'select',
                'field_name': 'industry',
                'field_label': 'Industry',
                'placeholder': 'Select your industry',
                'required': True,
                'options': [
                    'Technology',
                    'Manufacturing',
                    'Financial Services',
                    'Healthcare',
                    'Energy',
                    'Retail',
                    'Construction',
                    'Agriculture',
                    'Transportation',
                    'Other'
                ],
                'order': 3,
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('Created Industry Selection Form'))
        else:
            self.stdout.write(self.style.WARNING('Industry Selection Form already exists'))

        # ESG Priority Form
        priority_form, created = FormQuestion.objects.get_or_create(
            title="ESG Priority Assessment",
            defaults={
                'description': 'What are your main ESG priorities? Select all that apply.',
                'field_type': 'checkbox',
                'field_name': 'esg_priorities',
                'field_label': 'ESG Priorities',
                'placeholder': 'Select your priorities',
                'required': True,
                'options': [
                    'Environmental Sustainability',
                    'Social Responsibility',
                    'Corporate Governance',
                    'Climate Change Mitigation',
                    'Diversity and Inclusion',
                    'Supply Chain Ethics',
                    'Community Engagement',
                    'Employee Well-being',
                    'Transparency and Reporting',
                    'Risk Management'
                ],
                'order': 4,
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('Created ESG Priority Assessment Form'))
        else:
            self.stdout.write(self.style.WARNING('ESG Priority Assessment Form already exists'))

        # Contact Information Form
        contact_form, created = FormQuestion.objects.get_or_create(
            title="Contact Information",
            defaults={
                'description': 'Please provide your contact information for follow-up support.',
                'field_type': 'email',
                'field_name': 'contact_email',
                'field_label': 'Email Address',
                'placeholder': 'your.email@company.com',
                'required': True,
                'order': 5,
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('Created Contact Information Form'))
        else:
            self.stdout.write(self.style.WARNING('Contact Information Form already exists'))

        # Company Size Form
        size_form, created = FormQuestion.objects.get_or_create(
            title="Company Size",
            defaults={
                'description': 'What is the size of your company?',
                'field_type': 'radio',
                'field_name': 'company_size',
                'field_label': 'Company Size',
                'placeholder': 'Select company size',
                'required': True,
                'options': [
                    '1-10 employees',
                    '11-50 employees',
                    '51-200 employees',
                    '201-1000 employees',
                    '1000+ employees'
                ],
                'order': 6,
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('Created Company Size Form'))
        else:
            self.stdout.write(self.style.WARNING('Company Size Form already exists'))

        # ESG Reporting Timeline Form
        timeline_form, created = FormQuestion.objects.get_or_create(
            title="ESG Reporting Timeline",
            defaults={
                'description': 'When do you plan to start or improve your ESG reporting?',
                'field_type': 'date',
                'field_name': 'reporting_timeline',
                'field_label': 'Target Date for ESG Reporting',
                'placeholder': 'Select target date',
                'required': False,
                'order': 7,
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('Created ESG Reporting Timeline Form'))
        else:
            self.stdout.write(self.style.WARNING('ESG Reporting Timeline Form already exists'))

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully created/verified {FormQuestion.objects.filter(is_active=True).count()} sample forms.'
            )
        )
