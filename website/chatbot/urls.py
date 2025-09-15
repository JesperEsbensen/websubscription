from django.urls import path
from . import views

app_name = 'chatbot'

urlpatterns = [
    path('', views.chatbot_main, name='chatbot_main'),
    path('api/sessions/', views.get_sessions, name='get_sessions'),
    path('api/sessions/create/', views.create_session, name='create_session'),
    path('api/sessions/<int:session_id>/messages/', views.get_messages, name='get_messages'),
    path('api/sessions/<int:session_id>/clear/', views.clear_session, name='clear_session'),
    path('api/sessions/<int:session_id>/delete/', views.delete_session, name='delete_session'),
    path('api/messages/send/', views.send_message, name='send_message'),
    
    # Form-related URLs
    path('forms/<int:form_id>/', views.show_form, name='show_form'),
    path('api/forms/<int:form_id>/submit/', views.submit_form, name='submit_form'),
    path('api/forms/', views.get_available_forms, name='get_available_forms'),
    path('api/responses/', views.get_user_responses, name='get_user_responses'),
] 