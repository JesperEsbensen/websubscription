# Chatbot Form System

This document describes the form system integrated into the chatbot that allows users to fill out forms and have their responses stored in the database.

## Features

- **Dynamic Form Generation**: The chatbot can present forms to users based on their requests
- **Multiple Field Types**: Support for text, textarea, email, number, select, radio, checkbox, date, datetime, and file upload fields
- **Database Storage**: All form responses are stored in the database for easy retrieval
- **Admin Interface**: Forms can be managed through Django admin
- **Form Replacement**: After submission, forms are replaced with a summary of the stored data

## How It Works

### 1. Form Triggers
The chatbot automatically detects when users request forms based on keywords:
- "esg assessment" → ESG Assessment Form
- "company information" → Company Information Form
- "industry" → Industry Selection Form
- "esg priorities" → ESG Priority Assessment Form
- "contact" → Contact Information Form
- "company size" → Company Size Form
- "reporting timeline" → ESG Reporting Timeline Form
- "document upload" → Document Upload
- "upload document" → Document Upload
- "upload file" → Document Upload
- "upload" → Document Upload

### 2. Form Display
When a user requests a form, the chatbot presents it directly in the chat interface. Users can fill out and submit the form without leaving the chat.

### 3. Data Storage
When a form is submitted:
1. The response is saved to the database (`FormResponse` model)
2. The form is replaced with a summary of the submitted data

## Database Storage

Form responses are stored in the `FormResponse` model with the following structure:

- `user`: Foreign key to the User model
- `form_title`: Title of the form that was submitted
- `response_data`: JSON field containing all form responses
- `created_at`: Timestamp when the form was submitted
- `updated_at`: Timestamp when the record was last updated

## File Upload Support

The system supports file uploads with the following features:

### Supported File Types
The document upload form accepts the same file types that Docling can process:
- **Documents**: PDF, DOCX, PPTX, XLSX
- **Text Files**: MD, HTML, TXT, CSV
- **Images**: PNG, JPG, JPEG, TIFF, BMP, WEBP

### File Validation
- **File Size**: Maximum 50MB per file (configurable)
- **File Type**: Only allowed extensions are accepted
- **Security**: Files are validated before storage

### File Storage
- Files are stored in the `library/customers/<user_id>/` directory
- File metadata (name, size, type, path) is stored in the database
- Original filenames are preserved with timestamp to avoid conflicts
- Files are saved with format: `originalname_YYYYMMDD_HHMMSS.ext`

## Managing Forms

### Through Django Admin
1. Go to Django admin interface
2. Navigate to "Chatbot" → "Form questions"
3. Create, edit, or deactivate forms
4. View form responses in "Form responses"

### Through Management Command
Create sample forms:
```bash
python3 manage.py create_sample_forms
```

## API Endpoints

- `GET /chatbot/api/forms/` - Get all available forms
- `POST /chatbot/api/forms/<form_id>/submit/` - Submit a form
- `GET /chatbot/api/responses/` - Get user's form responses

## Usage Examples

### User Requesting a Form
User: "I need to fill out an ESG assessment form"
Bot: *Presents the ESG Assessment Form directly in the chat*

### User Requesting Document Upload
User: "I want to upload a document"
Bot: *Presents the Document Upload form with file picker*

### Form Submission
User fills out the form and clicks "Submit"
The form is replaced with a description showing:
- ✅ Form title and "Submitted" status
- List of all submitted responses with field labels
- Confirmation that data was saved to the database

## Customization

### Adding New Forms
1. Create a new `FormQuestion` object through Django admin
2. Set the appropriate field type, options, and validation rules
3. Add trigger keywords to the `check_for_form_request` function in `views.py`

### Modifying Form Triggers
Edit the `form_triggers` dictionary in the `check_for_form_request` function:

```python
form_triggers = {
    'your_keyword': 'Your Form Title',
    # ... existing triggers
}
```

### Custom Field Types
The system supports all standard HTML input types. To add custom field types:
1. Add the field type to `FormQuestion.FIELD_TYPES`
2. Update the `_generate_form_field_html` function to handle the new type

## Security Considerations

- All forms require user authentication
- CSRF protection is enabled for form submissions
- Form data is validated before storage
- Data is stored securely in the database

## Future Enhancements

- Form validation rules
- Multi-step forms
- Form templates
- Email notifications on form submission
- Form analytics and reporting
