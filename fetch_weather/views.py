from django.shortcuts import render, redirect
from django_htmx.http import HttpResponseClientRefresh
from django.contrib import messages
from django.http import HttpResponse
from fetch_weather.forms import LocationForm
from geopy.geocoders import Nominatim
import json
import requests
from pathlib import Path
import environ
import os
from .models import Location
from users.forms import UserPreferencesForm
from users.models import UserPreferences
from django.db.models import Q
import datetime, time
import re

BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))
API_KEY = env('API_KEY')


def home(request):
    context = {}
    if request.user.is_authenticated:
        try:
            max_order_num = Location.objects.filter(author=request.user).last().order
        except:
            max_order_num = 1
        if 'location' in request.POST:
            location = request.POST.get('location')
            if location == '':
                messages.warning(request, 'Please input a location.')
                return render(request, 'fetch_weather/home.html')
            geolocator = Nominatim(user_agent='http')
            location_validated = geolocator.geocode(location, addressdetails=True, language='en')
            if location_validated is None:
                messages.warning(request, f'{location} is not a valid location.')
                return render(request, 'fetch_weather/home.html')

            if 'city' in str(location_validated.raw['address']):
                city = str(location_validated.raw['address']['city'])
            elif 'town' in str(location_validated.raw['address']):
                city = str(location_validated.raw['address']['town'])
            elif 'village' in str(location_validated.raw['address']):
                city = str(location_validated.raw['address']['village'])
            elif 'county' in str(location_validated.raw['address']):
                city = str(location_validated.raw['address']['county'])
            elif 'province' in str(location_validated.raw['address']):
                city = str(location_validated.raw['address']['province'])
            else:
                city = ''
            state = str(
                location_validated.raw['address']['state']) if 'state' in str(
                location_validated.raw['address']) else ''
            country = str(
                location_validated.raw['address']['country']) if 'country' in str(
                location_validated.raw['address']) else ''
            if state == city:
                frontend_location = ', '.join([city, country])
            elif city == '':
                frontend_location = ', '.join([state, country])
            elif state == '':
                frontend_location = ', '.join([city, country])
            else:
                frontend_location = ', '.join([city, state, country])


            try:
                exists = Location.objects.filter(loc=frontend_location, author=request.user).first()
                time_from_request = datetime.datetime.fromtimestamp(exists.datetimeEpoch).timestamp()
                now = datetime.datetime.now().timestamp()
                if (now - time_from_request)/60 < 30:
                    messages.warning(request, f'Please wait {round(30 - ((now - time_from_request)/60))} minutes before updating.')
                    return render(request, 'fetch_weather/home.html')
                if exists:
                    messages.warning(request, f'{frontend_location} is already on your dashboard!')
                    return render(request, 'fetch_weather/home.html')
            except:
                pass

            url = (
                f'https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{frontend_location}'
                f'/next24hours?unitGroup=metric&timezone=America/New_York&elements=datetime%2CdatetimeEpoch%2Clatitude%2Clongitude%2C'
                f'tempmax%2Ctempmin%2Ctemp%2Cfeelslikemax%2Cfeelslikemin%2Cfeelslike%2Chumidity%2Cprecip%2Cpreciptype%2C'
                f'snow%2Cpressure%2Ccloudcover%2Cuvindex%2Csunrise%2Csunset%2Cmoonphase%2Cconditions%2Cdescription%2Cicon'
                f'&iconSet=icons2&key={API_KEY}&contentType=json')

            weather_data = requests.get(url).json()
            cc = weather_data['currentConditions']
            form_data = {'loc': frontend_location, 'datetime': cc['datetime'],
            'datetimeEpoch': cc['datetimeEpoch'], 'temp': cc['temp'], 'feelslike': cc['feelslike'],
            'humidity': cc['humidity'], 'precip': cc['precip'], 'snow': cc['snow'],
            'preciptype': cc['preciptype'], 'pressure': cc['pressure'], 'cloudcover': cc['cloudcover'],
            'uvindex': cc['uvindex'], 'conditions': cc['conditions'], 'icon': cc['icon'], 
            'sunrise': cc['sunrise'], 'sunset': cc['sunset'], 'moonphase': cc['moonphase'], 
            'daily_description': weather_data['description'], 'order': max_order_num, 'author': request.user}
            form = LocationForm(form_data)
            print(form.errors)
            if form.is_valid():
                form.save()
                messages.success(request, f'{frontend_location} successfully saved!')
                return HttpResponseClientRefresh()

        user_prefs, created = UserPreferences.objects.get_or_create(author=request.user, defaults={'units': 'us', 'timezone': 'America/New_York', 'author': request.user})
        units = user_prefs.units
        timezone = user_prefs.timezone
        all_timezones = {'America/New_York': 'America/New_York', 'America/Los_Angeles': 'America/Los_Angeles'}
        popped = all_timezones.pop(timezone)
        locations = list(Location.objects.filter(author=request.user).all().values())
        
        cards = {}
        
        if units == 'metric':
            front_units = {'temp_unit': '°C', 'precip_unit': 'mm', 'snow_unit': 'cm',
                        'wind_unit': 'km/h', 'visibility_unit': 'km', 'pressure_unit': 'mb'}
            for loc in locations:
                cards[loc['loc']] = {'datetime': loc['datetime'],
                'temp': loc['temp'], 'feelslike': loc['feelslike'],
                'humidity': loc['humidity'], 'precip': loc['precip'], 'snow': loc['snow'],
                'preciptype': loc['preciptype'], 'pressure': loc['pressure'], 'cloudcover': loc['cloudcover'],
                'uvindex': loc['uvindex'], 'conditions': loc['conditions'], 'icon': loc['icon'], 
                'sunrise': loc['sunrise'], 'sunset': loc['sunset'], 'moonphase': loc['moonphase'], 
                'daily_description': loc['daily_description'], 'last_modified': loc['last_modified']}
        elif units == 'uk':
            front_units = {'temp_unit': '°C', 'precip_unit': 'mm', 'snow_unit': 'cm',
                        'wind_unit': 'mph', 'visibility_unit': 'miles', 'pressure_unit': 'mb'}
            for loc in locations:
                cards[loc['loc']] = {'datetime': loc['datetime'],
                'temp': loc['temp'], 'feelslike': loc['feelslike'],
                'humidity': loc['humidity'], 'precip': loc['precip'], 'snow': loc['snow'],
                'preciptype': loc['preciptype'], 'pressure': loc['pressure'], 'cloudcover': loc['cloudcover'],
                'uvindex': loc['uvindex'], 'conditions': loc['conditions'], 'icon': loc['icon'], 
                'sunrise': loc['sunrise'], 'sunset': loc['sunset'], 'moonphase': loc['moonphase'], 
                'daily_description': loc['daily_description'], 'last_modified': loc['last_modified']}
        elif units == 'us':
            front_units = {'temp_unit': '°F', 'precip_unit': 'in', 'snow_unit': 'in',
                        'wind_unit': 'mph', 'visibility_unit': 'miles', 'pressure_unit': 'mb'}
            for loc in locations:
                cards[loc['loc']] = {'datetime': loc['datetime'],
                'temp': round((float(loc['temp'])*1.8)+32, 1), 'feelslike': round((float(loc['feelslike'])*1.8)+32, 1),
                'humidity': loc['humidity'], 'precip': round(float(loc['precip'])*25.4, 1), 'snow': round(float(loc['snow'])*2.54, 1),
                'preciptype': loc['preciptype'], 'pressure': loc['pressure'], 'cloudcover': loc['cloudcover'],
                'uvindex': loc['uvindex'], 'conditions': loc['conditions'], 'icon': loc['icon'], 
                'sunrise': loc['sunrise'], 'sunset': loc['sunset'], 'moonphase': loc['moonphase'], 
                'daily_description': loc['daily_description'], 'last_modified': loc['last_modified'],
                'pretty_loc': re.sub("[, ]", '_', loc['loc'])}

        context = {'saved_locs': cards, 'front_units': front_units, 'all_timezones': all_timezones, 'popped': popped}
    # else:
        # context = {}

    return render(request, 'fetch_weather/home.html', context)


def select_units(request):
    request_unit = request.GET.get('units')
    if request.user.is_authenticated:
        user_prefs, created = UserPreferences.objects.get_or_create(author=request.user,
        defaults={'units': 'us', 'timezone': 'America/New_York', 'author': request.user})
        timezone = user_prefs.timezone
        all_timezones = {'America/New_York': 'America/New_York', 'America/Los_Angeles': 'America/Los_Angeles'}
        popped = all_timezones.pop(timezone)
        unit_from_db = UserPreferences.objects.filter(author=request.user).first()
        valid_units = {'metric': 'Metric', 'us': 'US', 'uk': 'UK'}
        locations = list(Location.objects.filter(author=request.user).all().values())
        
        if request_unit in valid_units:
            cards = {}
            if request_unit == 'metric':
                units = {'temp_unit': '°C', 'precip_unit': 'mm', 'snow_unit': 'cm',
                        'wind_unit': 'km/h', 'visibility_unit': 'km', 'pressure_unit': 'mb'}
                unit_from_db.units = 'metric'
                unit_from_db.save()
                for loc in locations:
                    cards[loc['loc']] = {'datetime': loc['datetime'],
                    'temp': loc['temp'], 'feelslike': loc['feelslike'],
                    'humidity': loc['humidity'], 'precip': loc['precip'], 'snow': loc['snow'],
                    'preciptype': loc['preciptype'], 'pressure': loc['pressure'], 'cloudcover': loc['cloudcover'],
                    'uvindex': loc['uvindex'], 'conditions': loc['conditions'], 'icon': loc['icon'], 
                    'sunrise': loc['sunrise'], 'sunset': loc['sunset'], 'moonphase': loc['moonphase'], 
                    'daily_description': loc['daily_description']}
            elif request_unit == 'uk':
                units = {'temp_unit': '°C', 'precip_unit': 'mm', 'snow_unit': 'cm',
                            'wind_unit': 'mph', 'visibility_unit': 'miles', 'pressure_unit': 'mb'}
                unit_from_db.units = 'uk'
                unit_from_db.save()
                for loc in locations:
                    cards[loc['loc']] = {'datetime': loc['datetime'],
                    'temp': loc['temp'], 'feelslike': loc['feelslike'],
                    'humidity': loc['humidity'], 'precip': loc['precip'], 'snow': loc['snow'],
                    'preciptype': loc['preciptype'], 'pressure': loc['pressure'], 'cloudcover': loc['cloudcover'],
                    'uvindex': loc['uvindex'], 'conditions': loc['conditions'], 'icon': loc['icon'], 
                    'sunrise': loc['sunrise'], 'sunset': loc['sunset'], 'moonphase': loc['moonphase'], 
                    'daily_description': loc['daily_description']}
            elif request_unit == 'us':
                units = {'temp_unit': '°F', 'precip_unit': 'in', 'snow_unit': 'in',
                            'wind_unit': 'mph', 'visibility_unit': 'miles', 'pressure_unit': 'mb'}
                unit_from_db.units = 'us'
                unit_from_db.save()
                for loc in locations:
                    cards[loc['loc']] = {'datetime': loc['datetime'],
                    'temp': round((float(loc['temp'])*1.8)+32, 1), 'feelslike': round((float(loc['feelslike'])*1.8)+32, 1),
                    'humidity': loc['humidity'], 'precip': round(float(loc['precip'])*25.4, 1), 'snow': round(float(loc['snow'])*2.54, 1),
                    'preciptype': loc['preciptype'], 'pressure': loc['pressure'], 'cloudcover': loc['cloudcover'],
                    'uvindex': loc['uvindex'], 'conditions': loc['conditions'], 'icon': loc['icon'], 
                    'sunrise': loc['sunrise'], 'sunset': loc['sunset'], 'moonphase': loc['moonphase'], 
                    'daily_description': loc['daily_description']}
        else:
            context = {}
            units = {}
        context = {'saved_locs': cards, 'units': units, 'all_timezones': all_timezones, 'popped': popped}
    if request.htmx:
        return HttpResponseClientRefresh()
        #return render(request, 'fetch_weather/partials/units.html', context)
    return render(request, 'fetch_weather/home.html', context)

def add_card(request):
    context = {}
    try:
        max_order_num = Location.objects.filter(author=request.user).last().order + 1
    except:
        max_order_num = 1
    if request.htmx:
        location = request.POST.get('location')
        if location == '':
            messages.warning(request, 'Please input a location.')
            return HttpResponseClientRefresh()
        geolocator = Nominatim(user_agent='http')
        location_validated = geolocator.geocode(location, addressdetails=True, language='en')
        if location_validated is None:
            messages.warning(request, f'{location} is not a valid location.')
            return HttpResponseClientRefresh()

        if 'city' in str(location_validated.raw['address']):
            city = str(location_validated.raw['address']['city'])
        elif 'town' in str(location_validated.raw['address']):
            city = str(location_validated.raw['address']['town'])
        elif 'village' in str(location_validated.raw['address']):
            city = str(location_validated.raw['address']['village'])
        elif 'county' in str(location_validated.raw['address']):
            city = str(location_validated.raw['address']['county'])
        elif 'province' in str(location_validated.raw['address']):
            city = str(location_validated.raw['address']['province'])
        else:
            city = ''
        state = str(
            location_validated.raw['address']['state']) if 'state' in str(
            location_validated.raw['address']) else ''
        country = str(
            location_validated.raw['address']['country']) if 'country' in str(
            location_validated.raw['address']) else ''
        if state == city:
            frontend_location = ', '.join([city, country])
        elif city == '':
            frontend_location = ', '.join([state, country])
        elif state == '':
            frontend_location = ', '.join([city, country])
        else:
            frontend_location = ', '.join([city, state, country])


        try:
            exists = Location.objects.filter(loc=frontend_location, author=request.user).first()
            time_from_request = datetime.datetime.fromtimestamp(exists.datetimeEpoch).timestamp()
            now = datetime.datetime.now().timestamp()
            if (now - time_from_request)/60 < 30:
                messages.warning(request, f'Please wait {round(30 - ((now - time_from_request)/60))} minutes before updating.')
                return HttpResponseClientRefresh()
            if exists:
                messages.warning(request, f'{frontend_location} is already on your dashboard!')
                return HttpResponseClientRefresh()
        except:
            pass

        url = (
            f'https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{frontend_location}'
            f'/next24hours?unitGroup=metric&timezone=America/New_York&elements=datetime%2CdatetimeEpoch%2Clatitude%2Clongitude%2C'
            f'tempmax%2Ctempmin%2Ctemp%2Cfeelslikemax%2Cfeelslikemin%2Cfeelslike%2Chumidity%2Cprecip%2Cpreciptype%2C'
            f'snow%2Cpressure%2Ccloudcover%2Cuvindex%2Csunrise%2Csunset%2Cmoonphase%2Cconditions%2Cdescription%2Cicon'
            f'&iconSet=icons2&key={API_KEY}&contentType=json')

        weather_data = requests.get(url).json()
        cc = weather_data['currentConditions']
        form_data = {'loc': frontend_location, 'datetime': cc['datetime'],
        'datetimeEpoch': cc['datetimeEpoch'], 'temp': cc['temp'], 'feelslike': cc['feelslike'],
        'humidity': cc['humidity'], 'precip': cc['precip'], 'snow': cc['snow'],
        'preciptype': cc['preciptype'], 'pressure': cc['pressure'], 'cloudcover': cc['cloudcover'],
        'uvindex': cc['uvindex'], 'conditions': cc['conditions'], 'icon': cc['icon'], 
        'sunrise': cc['sunrise'], 'sunset': cc['sunset'], 'moonphase': cc['moonphase'], 
        'daily_description': weather_data['description'], 'order': max_order_num, 'author': request.user}
        form = LocationForm(form_data)
        print(form.errors)
        if form.is_valid():
            form.save()
            messages.success(request, f'{frontend_location} successfully saved!')
            return HttpResponseClientRefresh()

        user_prefs, created = UserPreferences.objects.get_or_create(author=request.user,
        defaults={'units': 'us', 'timezone': 'America/New_York', 'author': request.user})
        units = user_prefs.units
        timezone = user_prefs.timezone
        all_timezones = {'America/New_York': 'America/New_York', 'America/Los_Angeles': 'America/Los_Angeles'}
        popped = all_timezones.pop(timezone)
        locations = list(Location.objects.filter(author=request.user).all().values())
        cards = {}
        for loc in locations:
                    cards[loc['loc']] = {'datetime': loc['datetime'],
                    'temp': loc['temp'], 'feelslike': loc['feelslike'],
                    'humidity': loc['humidity'], 'precip': loc['precip'], 'snow': loc['snow'],
                    'preciptype': loc['preciptype'], 'pressure': loc['pressure'], 'cloudcover': loc['cloudcover'],
                    'uvindex': loc['uvindex'], 'conditions': loc['conditions'], 'icon': loc['icon'], 
                    'sunrise': loc['sunrise'], 'sunset': loc['sunset'], 'moonphase': loc['moonphase'], 
                    'daily_description': loc['daily_description']}
        context = {'saved_locs': cards}
        
        
        if units == 'metric':
            front_units = {'temp_unit': '°C', 'precip_unit': 'mm', 'snow_unit': 'cm',
                        'wind_unit': 'km/h', 'visibility_unit': 'km', 'pressure_unit': 'mb'}
            for loc in locations:
                cards[loc['loc']] = {'datetime': loc['datetime'],
                'temp': loc['temp'], 'feelslike': loc['feelslike'],
                'humidity': loc['humidity'], 'precip': loc['precip'], 'snow': loc['snow'],
                'preciptype': loc['preciptype'], 'pressure': loc['pressure'], 'cloudcover': loc['cloudcover'],
                'uvindex': loc['uvindex'], 'conditions': loc['conditions'], 'icon': loc['icon'], 
                'sunrise': loc['sunrise'], 'sunset': loc['sunset'], 'moonphase': loc['moonphase'], 
                'daily_description': loc['daily_description']}
        elif units == 'uk':
            front_units = {'temp_unit': '°C', 'precip_unit': 'mm', 'snow_unit': 'cm',
                        'wind_unit': 'mph', 'visibility_unit': 'miles', 'pressure_unit': 'mb'}
            for loc in locations:
                cards[loc['loc']] = {'datetime': loc['datetime'],
                'temp': loc['temp'], 'feelslike': loc['feelslike'],
                'humidity': loc['humidity'], 'precip': loc['precip'], 'snow': loc['snow'],
                'preciptype': loc['preciptype'], 'pressure': loc['pressure'], 'cloudcover': loc['cloudcover'],
                'uvindex': loc['uvindex'], 'conditions': loc['conditions'], 'icon': loc['icon'], 
                'sunrise': loc['sunrise'], 'sunset': loc['sunset'], 'moonphase': loc['moonphase'], 
                'daily_description': loc['daily_description']}
        elif units == 'us':
            front_units = {'temp_unit': '°F', 'precip_unit': 'in', 'snow_unit': 'in',
                        'wind_unit': 'mph', 'visibility_unit': 'miles', 'pressure_unit': 'mb'}
            for loc in locations:
                    cards[loc['loc']] = {'datetime': loc['datetime'],
                    'temp': round((float(loc['temp'])*1.8)+32, 1), 'feelslike': round((float(loc['feelslike'])*1.8)+32, 1),
                    'humidity': loc['humidity'], 'precip': round(float(loc['precip'])*25.4, 1), 'snow': round(float(loc['snow'])*2.54, 1),
                    'preciptype': loc['preciptype'], 'pressure': loc['pressure'], 'cloudcover': loc['cloudcover'],
                    'uvindex': loc['uvindex'], 'conditions': loc['conditions'], 'icon': loc['icon'], 
                    'sunrise': loc['sunrise'], 'sunset': loc['sunset'], 'moonphase': loc['moonphase'], 
                    'daily_description': loc['daily_description']}
        return render(request, 'fetch_weather/partials/add_card.html', context)

    context = {'saved_locs': cards, 'front_units': front_units, 'all_timezones': all_timezones, 'popped': popped}
    
        
    #eturn render(request, 'fetch_weather/home.html', context)

def remove_card(request):
    if request.user.is_authenticated:
        loc = request.POST
        new_loc = []
        for item in loc:
            new_loc.append(item)
        loc = ', '.join(new_loc)
        x = Location.objects.filter(author=request.user).get(loc=loc)
        x.delete()
        messages.success(request, f'Successfully deleted {x.loc}!')

def sort(request):
    if request.user.is_authenticated:
        locations = list(Location.objects.filter(author=request.user).all().values())
        card_order = dict(request.POST)
        card_order = card_order['card-order']
        user_prefs, created = UserPreferences.objects.get_or_create(author=request.user,
        defaults={'units': 'us', 'timezone': 'America/New_York', 'author': request.user})
        units = user_prefs.units
        timezone = user_prefs.timezone
        all_timezones = {'America/New_York': 'America/New_York', 'America/Los_Angeles': 'America/Los_Angeles'}
        popped = all_timezones.pop(timezone)

        sorted_cards = {}
        cards = {}
        if units == 'metric' or units == 'uk':
            for loc in locations:
                cards[loc['loc']] = {'datetime': loc['datetime'],
                'temp': loc['temp'], 'feelslike': loc['feelslike'],
                'humidity': loc['humidity'], 'precip': loc['precip'], 'snow': loc['snow'],
                'preciptype': loc['preciptype'], 'pressure': loc['pressure'], 'cloudcover': loc['cloudcover'],
                'uvindex': loc['uvindex'], 'conditions': loc['conditions'], 'icon': loc['icon'], 
                'sunrise': loc['sunrise'], 'sunset': loc['sunset'], 'moonphase': loc['moonphase'], 
                'daily_description': loc['daily_description']}
        elif units == 'us':
            for loc in locations:
                cards[loc['loc']] = {'datetime': loc['datetime'],
                'temp': round((float(loc['temp'])*1.8)+32, 1), 'feelslike': round((float(loc['feelslike'])*1.8)+32, 1),
                'humidity': loc['humidity'], 'precip': round(float(loc['precip'])*25.4, 1), 'snow': round(float(loc['snow'])*2.54, 1),
                'preciptype': loc['preciptype'], 'pressure': loc['pressure'], 'cloudcover': loc['cloudcover'],
                'uvindex': loc['uvindex'], 'conditions': loc['conditions'], 'icon': loc['icon'], 
                'sunrise': loc['sunrise'], 'sunset': loc['sunset'], 'moonphase': loc['moonphase'], 
                'daily_description': loc['daily_description']}

        for count, sorted_loc in enumerate(card_order):
            sorted_cards[sorted_loc] = cards[sorted_loc]
            loc1 = Location.objects.get(author=request.user, loc=sorted_loc)
            loc1.order = count + 1
            loc1.save(update_fields=['order'])

        if units == 'metric':
            front_units = {'temp_unit': '°C', 'precip_unit': 'mm', 'snow_unit': 'cm',
                        'wind_unit': 'km/h', 'visibility_unit': 'km', 'pressure_unit': 'mb'}
        elif units == 'uk':
            front_units = {'temp_unit': '°C', 'precip_unit': 'mm', 'snow_unit': 'cm',
                        'wind_unit': 'mph', 'visibility_unit': 'miles', 'pressure_unit': 'mb'}
        elif units == 'us':
            front_units = {'temp_unit': '°F', 'precip_unit': 'in', 'snow_unit': 'in',
                        'wind_unit': 'mph', 'visibility_unit': 'miles', 'pressure_unit': 'mb'}

        context = {'saved_locs': sorted_cards, 'front_units': front_units}
        return render(request, 'fetch_weather/partials/sort.html', context)


def select_timezone(request):
    context = {}
    request_tz = request.GET.get('timezone')
    if request.user.is_authenticated:
        user_prefs, created = UserPreferences.objects.get_or_create(author=request.user,
        defaults={'units': 'us', 'timezone': 'America/New_York', 'author': request.user})
        locations = list(Location.objects.filter(author=request.user).all().values())
        timezone = user_prefs.timezone
        all_timezones = {'America/New_York': 'America/New_York', 'America/Los_Angeles': 'America/Los_Angeles'}
        

        user_prefs.timezone = request_tz if request_tz in all_timezones else user_prefs.timezone
        user_prefs.save()

        popped = all_timezones.pop(user_prefs.timezone)

        context = {'all_timezones': all_timezones, 'popped': popped}

    if request.htmx:
        return render(request, 'fetch_weather/partials/timezone.html', context)
    return render(request, 'fetch_weather/home.html', context)

def about(request):
    return render(request, 'fetch_weather/about.html')


def past(request):
    return render(request, 'fetch_weather/past.html')


class Loc():
    '''Cleans up the home function, all of the location processing is done in this class'''

    def __init__(self, request, location, author):
        self.request = request
        self.location = location
        self.author = author
        geolocator = Nominatim(user_agent='http')
        self.location = geolocator.geocode(self.location, addressdetails=True, language='en')
        # TODO - add functionality for anonymous users.

    def is_valid(self):
        '''Uses Nominatim api, if the request returns none then we know the location is not a true input.'''
        if self.location is None:
            return False
        else:
            return True

    def clean_location(self):
        '''Returns the city, state, country where if the city, state, or province match then it will only return the city, country.
           This is stored in the database and will be displayed on the user's page.'''
        if 'city' in str(self.location.raw['address']):
            city = str(self.location.raw['address']['city'])
        elif 'town' in str(self.location.raw['address']):
            city = str(self.location.raw['address']['town'])
        elif 'village' in str(self.location.raw['address']):
            city = str(self.location.raw['address']['village'])
        else:
            city = ''
        state = str(self.location.raw['address']['state']) if 'state' in str(self.location.raw['address']) else 'no'
        country = str(
            self.location.raw['address']['country']) if 'country' in str(
            self.location.raw['address']) else 'no'
        if state == city:
            self.location = ', '.join([city, country])
        else:
            self.location = ', '.join([city, state, country])
        return self.location

    def update_current_weather(self, request_unit):
        '''Makes an api call to update the weather. Also formats the incoming data into the way an end user should see.'''
        self.units = request_unit
        timezone = 'America/New_York'
        url = (
            f'https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{self.location}'
            f'/next24hours?unitGroup={units}&timezone={timezone}&elements=datetime%2CdatetimeEpoch%2Clatitude%2Clongitude%2C'
            f'tempmax%2Ctempmin%2Ctemp%2Cfeelslikemax%2Cfeelslikemin%2Cfeelslike%2Chumidity%2Cprecip%2Cpreciptype%2C'
            f'snow%2Cpressure%2Ccloudcover%2Cuvindex%2Csunrise%2Csunset%2Cmoonphase%2Cconditions%2Cdescription%2Cicon'
            f'&iconSet=icons2&include=hours%2Ccurrent%2Cdays&key={API_KEY}&contentType=json')

        if request_unit == 'metric':
            units = {'temp_unit': '°C', 'precip_unit': 'mm', 'snow_unit': 'cm',
                     'wind_unit': 'km/h', 'visibility_unit': 'km', 'pressure_unit': 'mb'}
        elif request_unit == 'uk':
            units = {'temp_unit': '°C', 'precip_unit': 'mm', 'snow_unit': 'cm',
                     'wind_unit': 'mph', 'visibility_unit': 'miles', 'pressure_unit': 'mb'}
        else:
            units = {'temp_unit': '°F', 'precip_unit': 'in', 'snow_unit': 'in',
                     'wind_unit': 'mph', 'visibility_unit': 'miles', 'pressure_unit': 'mb'}

        location_api_data = requests.get(url).json()
        current_conditions = location_api_data['currentConditions']

        sunrise = current_conditions['sunrise'][:-3]
        if int(sunrise[:2]) == 12:
            sunrise = '12' + sunrise[2:] + ' PM'
        elif int(sunrise[:2]) == 00:
            sunrise = '12' + sunrise[2:] + ' AM'
        elif int(sunrise[0]) == 0 and int(sunrise[:2]) != 00:
            sunrise = sunrise[1:]
            if int(sunrise[0]) < 12:
                sunrise += ' AM'
        elif int(sunrise[:2]) < 12:
            sunrise += ' AM'
        elif int(sunrise[:2]) > 12:
            sunrise = str(int(sunrise[:2]) - 12) + sunrise[2:] + ' PM'

        sunset = current_conditions['sunset'][:-3]
        if int(sunset[:2]) == 12:
            sunset = '12' + sunset[2:] + ' PM'
        elif int(sunset[:2]) == 00:
            sunset = '12' + sunset[2:] + ' AM'
        elif int(sunset[0]) == 0 and int(sunset[:2]) != 00:
            sunset = sunset[1:]
            if int(sunset[0]) < 12:
                sunset += ' AM'
        elif int(sunset[:2]) < 12:
            sunset += ' AM'
        elif int(sunset[:2]) > 12:
            sunset = str(int(sunset[:2]) - 12) + sunset[2:] + ' PM'

        frontend_current_weather = {}
        frontend_current_weather['Feels Like'] = str(current_conditions['feelslike']) + units['temp_unit']
        frontend_current_weather['Precip'] = str(current_conditions['precip']) + units['precip_unit']
        if current_conditions['preciptype'] is not None:
            preciptypes = [x.capitalize() for x in current_conditions['preciptype']]
            frontend_current_weather['Precip Type'] = ', '.join(preciptypes)
        else:
            frontend_current_weather['Precip type'] = 'None'
        frontend_current_weather['Snow'] = str(current_conditions['snow']) + units['snow_unit']
        frontend_current_weather['Humidity'] = str(current_conditions['humidity']) + '%'
        frontend_current_weather['Cloud Cover'] = str(current_conditions['cloudcover']) + '%'
        frontend_current_weather['UV Index'] = str(current_conditions['uvindex'])
        frontend_current_weather['Pressure'] = str(current_conditions['pressure']) + units['pressure_unit']
        frontend_current_weather['Sunrise'] = sunrise
        frontend_current_weather['Sunset'] = sunset
        return frontend_current_weather

#     def convert_to_us(request):
#         pass

        #     if request.method == 'POST':
        #     form = LocationForm(request.POST)
        #     if form.is_valid():
        #         location = request.POST.get('location')
        #         units_type = request.POST.get('units')
        #         timezone = request.POST.get('timezone')
        #         if location == '':
        #             messages.warning(request, 'Please input a location.')
        #             return render(request, 'fetch_weather/home.html')

        #         geolocator = Nominatim(user_agent='http')
        #         try:
        #             lat, lon = location.split(',')
        #             if isinstance(lat, float) and isinstance(lon, float):
        #                 location = geolocator.reverse((lat, lon))
        #             else:
        #                 location = geolocator.geocode(location, addressdetails=True, language='en')
        #                 lat = str(round(location.latitude, 4))
        #                 lon = str(round(location.longitude, 4))
        #                 if 'city' in str(location.raw['address']):
        #                     city = str(location.raw['address']['city'])
        #                 elif 'town' in str(location.raw['address']):
        #                     city = str(location.raw['address']['town'])
        #                 elif 'village' in str(location.raw['address']):
        #                     city = str(location.raw['address']['village'])
        #                 else:
        #                     city = ''
        #                 state = str(location.raw['address']['state']) if 'state' in str(location.raw['address']) else ''
        #                 country = str(location.raw['address']['country']) if 'country' in str(location.raw['address']) else ''
        #         except:
        #             messages.warning(request, 'Invalid location.')
        #             return render(request, 'fetch_weather/home.html')

        #         if state == city:
        #             frontend_location = ', '.join([city, country])
        #         else:
        #             frontend_location = ', '.join([city, state, country])

        #         url = f'https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{frontend_location}/next24hours?unitGroup={units_type}&timezone={timezone}&elements=datetime%2Clatitude%2Clongitude%2Ctempmax%2Ctempmin%2Ctemp%2Cfeelslikemax%2Cfeelslikemin%2Cfeelslike%2Chumidity%2Cprecip%2Cpreciptype%2Csnow%2Cpressure%2Ccloudcover%2Cuvindex%2Csunrise%2Csunset%2Cmoonphase%2Cconditions%2Cdescription%2Cicon&iconSet=icons2&include=hours%2Ccurrent%2Cdays&key={API_KEY}&contentType=json'

        #         if request.user.is_authenticated:
        #             temperature = 100

        #         location_api_data = requests.get(url).json()
        #         current_weather = location_api_data['currentConditions']
        #         current_weather = {'datetime': '20:20:11', 'temp': 15.7, 'feelslike': 15.7, 'humidity': 35.8, 'precip': 0.0, 'preciptype': ['snow', 'rain', 'ice'], 'pressure': 1024.0, 'cloudcover': 0.0, 'uvindex': 0.0, 'conditions': 'Clear', 'icon': 'clear-day', 'sunrise': '13:55:07', 'sunset': '20:15:27', 'moonphase': 0.05, 'snow' : 0.5}
        #         description = 'Cloudy skies throughout the day.'
        #         description = current_weather['conditions']
        #         icon = f'https://raw.githubusercontent.com/visualcrossing/WeatherIcons/main/SVG/1st%20Set%20-%20Color/{current_weather["icon"]}.svg'
        #         if units_type == 'metric':
        #             units = {'temp_unit' : '°C', 'precip_unit' : 'mm', 'snow_unit' : 'cm', 'wind_unit' : 'km/h', 'visibility_unit' : 'km', 'pressure_unit' : 'mb'}
        #         elif units_type == 'uk':
        #             units = {'temp_unit' : '°C', 'precip_unit' : 'mm', 'snow_unit' : 'cm', 'wind_unit' : 'mph', 'visibility_unit' : 'miles', 'pressure_unit' : 'mb'}
        #         else:
        #             units = {'temp_unit' : '°F', 'precip_unit' : 'in', 'snow_unit' : 'in', 'wind_unit' : 'mph', 'visibility_unit' : 'miles', 'pressure_unit' : 'mb'}

        #         sunrise = current_weather['sunrise'][:-3]
        #         if int(sunrise[:2]) == 12:
        #             sunrise = '12' + sunrise[2:] + ' PM'
        #         elif int(sunrise[:2]) == 00:
        #             sunrise = '12' + sunrise[2:] + ' AM'
        #         elif int(sunrise[0]) == 0 and int(sunrise[:2]) != 00:
        #             sunrise = sunrise[1:]
        #             if int(sunrise[0]) < 12:
        #                 sunrise += ' AM'
        #         elif int(sunrise[:2]) < 12:
        #             sunrise += ' AM'
        #         elif int(sunrise[:2]) > 12:
        #             sunrise = str(int(sunrise[:2]) - 12) + sunrise[2:] + ' PM'

        #         sunset = current_weather['sunset'][:-3]
        #         if int(sunset[:2]) == 12:
        #             sunset = '12' + sunset[2:] + ' PM'
        #         elif int(sunset[:2]) == 00:
        #             sunset = '12' + sunset[2:] + ' AM'
        #         elif int(sunset[0]) == 0 and int(sunset[:2]) != 00:
        #             sunset = sunset[1:]
        #             if int(sunset[0]) < 12:
        #                 sunset += ' AM'
        #         elif int(sunset[:2]) < 12:
        #             sunset += ' AM'
        #         elif int(sunset[:2]) > 12:
        #             sunset = str(int(sunset[:2]) - 12) + sunset[2:] + ' PM'

        #         frontend_current_weather = {}
        #         frontend_current_weather['Feels Like'] = str(current_weather['feelslike']) + units['temp_unit']
        #         frontend_current_weather['Precip'] = str(current_weather['precip']) + units['precip_unit']
        #         if current_weather['preciptype'] is not None:
        #             preciptypes = [x.capitalize() for x in current_weather['preciptype']]
        #             frontend_current_weather['Precip Type'] = ', '.join(preciptypes)
        #         else:
        #             frontend_current_weather['Precip type'] = 'None'
        #         frontend_current_weather['Snow'] = str(current_weather['snow']) + units['snow_unit']
        #         frontend_current_weather['Humidity'] = str(current_weather['humidity']) + '%'
        #         frontend_current_weather['Cloud Cover'] = str(current_weather['cloudcover']) + '%'
        #         frontend_current_weather['UV Index'] = str(current_weather['uvindex'])
        #         frontend_current_weather['Pressure'] = str(current_weather['pressure']) + units['pressure_unit']
        #         frontend_current_weather['Sunrise'] = sunrise
        #         frontend_current_weather['Sunset'] = sunset

        #         location_current_weather_data = {'current_conditions': frontend_current_weather, 'location': frontend_location, 'units': units, 'description':description, 'icon' : icon, 'temp' : current_weather['temp'], 'conditions' : current_weather['conditions']}
        #         request.user.location_set.create(loc=frontend_location, units=units, timezone=timezone)
        #     else:
        #         location_current_weather_data = {}
        # else:
        #     location_current_weather_data = {}
        # context = {'location_current_weather_data' : location_current_weather_data}
