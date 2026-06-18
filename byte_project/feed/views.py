from django.shortcuts import render

def home(request):
    return render(request, 'feed/home.html')

def explore(request):
    return render(request, 'feed/explore.html')

def messages(request):
    return render(request, 'feed/messages.html')

def profile(request):
    return render(request, 'feed/profile.html')
