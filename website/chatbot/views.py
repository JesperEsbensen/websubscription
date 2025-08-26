from django.shortcuts import render

# Create your views here.

# Main page view for the chatbot app
def chatbot_main(request):
    return render(request, 'chatbot/main.html')
