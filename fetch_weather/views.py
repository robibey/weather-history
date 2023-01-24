from django.shortcuts import render
from django.contrib import messages
from django.http import HttpResponse
from fetch_weather.forms import LocationForm
from geopy.geocoders import Nominatim
import json
from django.utils import timezone

def home(request):
    if request.method == 'POST':
        location = request.POST.get('location')
        units_type = request.POST.get('units')
        timezone = request.POST.get('timezone')
        if location == '':
            messages.warning(request, 'Please input a location.')
            return render(request, 'fetch_weather/home.html')
            
        geolocator = Nominatim(user_agent='http')
        try:
            new_location = geolocator.geocode(location)
            lat = str(round(new_location.latitude, 4))
            lon = str(round(new_location.longitude, 4))
        except:
            messages.warning(request, 'Invalid location.')
            return render(request, 'fetch_weather/home.html')

        url = f''

        #if request.user.is_authenticated:
            #temperature = 100
        location_current_weather_data = {'city': (lat, lon), 'temperature': 5, 'units':units_type}
    else:
        location_current_weather_data = {}
    context = {'location_current_weather_data' : location_current_weather_data}
    return render(request, 'fetch_weather/home.html', context)

def about(request):
    return render(request, 'fetch_weather/about.html')

def past(request):
    return render(request, 'fetch_weather/past.html')
