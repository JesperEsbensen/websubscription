"""Test utility functions and helpers."""

import tempfile
import os
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings

class TestDataHelper:
    """Helper class for creating test data."""
    
    @staticmethod
    def create_test_image(filename='test.jpg', size=(100, 100)):
        """Create a test image file for upload testing."""
        from PIL import Image
        import io
        
        image = Image.new('RGB', size, color='red')
        image_file = io.BytesIO()
        image.save(image_file, format='JPEG')
        image_file.seek(0)
        
        return SimpleUploadedFile(
            filename,
            image_file.getvalue(),
            content_type='image/jpeg'
        )
    
    @staticmethod
    def create_test_pdf(filename='test.pdf', content='Test PDF content'):
        """Create a test PDF file for upload testing."""
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        import io
        
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        p.drawString(100, 750, content)
        p.save()
        buffer.seek(0)
        
        return SimpleUploadedFile(
            filename,
            buffer.getvalue(),
            content_type='application/pdf'
        )
    
    @staticmethod
    def create_temp_directory():
        """Create a temporary directory for testing."""
        return tempfile.mkdtemp()

class StripeTestHelper:
    """Helper class for mocking Stripe responses."""
    
    @staticmethod
    def mock_customer_response(customer_id='cus_test123', email='test@example.com'):
        """Create a mock Stripe customer response."""
        return {
            'id': customer_id,
            'email': email,
            'created': 1234567890,
            'default_source': None,
            'subscriptions': {'data': []}
        }
    
    @staticmethod
    def mock_subscription_response(sub_id='sub_test123', customer_id='cus_test123'):
        """Create a mock Stripe subscription response."""
        return {
            'id': sub_id,
            'customer': customer_id,
            'status': 'active',
            'current_period_start': 1234567890,
            'current_period_end': 1234567890 + 2592000,
            'items': {'data': [{
                'price': {'id': 'price_test123'}
            }]}
        }
    
    @staticmethod
    def mock_webhook_event(event_type='customer.subscription.created', data=None):
        """Create a mock Stripe webhook event."""
        if data is None:
            data = StripeTestHelper.mock_subscription_response()
        
        return {
            'id': 'evt_test123',
            'type': event_type,
            'created': 1234567890,
            'data': {'object': data}
        }