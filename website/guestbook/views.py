from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Comment
from .forms import CommentForm

def guestbook_list(request):
    """Display all comments in the guest book"""
    comments = Comment.objects.all()
    form = CommentForm()
    
    if request.method == 'POST' and request.user.is_authenticated:
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.save()
            messages.success(request, 'Your comment has been added successfully!')
            return redirect('guestbook:guestbook_list')
    
    context = {
        'comments': comments,
        'form': form,
    }
    return render(request, 'guestbook/guestbook_list.html', context)

@login_required
def add_comment(request):
    """Add a new comment (AJAX endpoint)"""
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.save()
            return JsonResponse({
                'success': True,
                'message': 'Comment added successfully!',
                'comment': {
                    'author': comment.author.username,
                    'content': comment.content,
                    'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M'),
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})
