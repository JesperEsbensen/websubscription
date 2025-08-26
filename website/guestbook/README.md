# Guest Book App

This Django app provides a guest book functionality where users can add and view comments.

## Features

- **View Comments**: Anyone can view all comments in the guest book
- **Add Comments**: Authenticated users can add new comments
- **User-friendly Interface**: Modern Bootstrap-based UI with responsive design
- **Admin Interface**: Comments can be managed through Django admin
- **Form Validation**: Proper validation for comment content (max 1000 characters)

## Models

### Comment
- `author`: ForeignKey to User (who wrote the comment)
- `content`: TextField (the comment content, max 1000 characters)
- `created_at`: DateTimeField (when the comment was created)
- `updated_at`: DateTimeField (when the comment was last updated)

## Views

- `guestbook_list`: Main view that displays all comments and handles comment submission
- `add_comment`: AJAX endpoint for adding comments (for future enhancement)

## URLs

- `/guestbook/`: Main guest book page
- `/guestbook/add-comment/`: AJAX endpoint for adding comments

## Templates

- `guestbook/guestbook_list.html`: Main template displaying comments and comment form

## Navigation

The guest book is accessible via:
- **Top Navigation**: "Guest Book" button in the main navigation bar (for authenticated users)
- **Footer**: "Guest Book" link in the footer (for all users)

## Testing

Run tests with:
```bash
python manage.py test guestbook
```

## Admin Interface

Comments can be managed through the Django admin interface at `/admin/guestbook/comment/`.

## Future Enhancements

- AJAX comment submission for better user experience
- Comment editing and deletion for comment authors
- Comment moderation features
- Rich text formatting for comments
- Comment replies/threading
