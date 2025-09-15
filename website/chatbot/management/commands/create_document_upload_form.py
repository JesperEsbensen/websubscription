from django.core.management.base import BaseCommand
from chatbot.models import FormQuestion


class Command(BaseCommand):
    help = 'Create document upload form for the chatbot'

    def handle(self, *args, **options):
        # Document Upload Form
        doc_upload_form, created = FormQuestion.objects.get_or_create(
            title="Document Upload",
            defaults={
                'description': 'Upload documents for processing and analysis. Supported formats: PDF, DOCX, PPTX, XLSX, MD, HTML, TXT, CSV, and image files (PNG, JPG, JPEG, TIFF, BMP, WEBP).',
                'field_type': 'file',
                'field_name': 'document_upload',
                'field_label': 'Select Document to Upload',
                'placeholder': 'Choose a file to upload',
                'required': True,
                'order': 8,
                'is_active': True,
                'validation_rules': {
                    'max_size': '50MB',
                    'allowed_types': [
                        'application/pdf',
                        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                        'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                        'text/markdown',
                        'text/html',
                        'text/plain',
                        'text/csv',
                        'image/png',
                        'image/jpeg',
                        'image/tiff',
                        'image/bmp',
                        'image/webp'
                    ],
                    'allowed_extensions': [
                        '.pdf', '.docx', '.pptx', '.xlsx',
                        '.md', '.markdown', '.html', '.htm', '.txt', '.csv',
                        '.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.webp'
                    ]
                }
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('Created Document Upload Form'))
        else:
            self.stdout.write(self.style.WARNING('Document Upload Form already exists'))

        self.stdout.write(
            self.style.SUCCESS(
                f'\nDocument upload form created/verified successfully.'
            )
        )
