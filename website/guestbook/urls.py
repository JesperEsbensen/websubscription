from django.urls import path
from . import views

app_name = 'guestbook'

urlpatterns = [
    path('', views.guestbook_list, name='guestbook_list'),
    path('add-comment/', views.add_comment, name='add_comment'),
]
