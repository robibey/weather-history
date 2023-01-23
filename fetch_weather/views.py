from django.shortcuts import render
from django.http import HttpResponse

def home(request):
    return render(request, 'fetch_weather/home.html')

def about(request):
    return render(request, 'fetch_weather/about.html')