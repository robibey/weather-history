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
from django.db.models import Q, Count
import datetime, time
import re
from django.utils import timezone


BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))
API_KEY = env('API_KEY')

METRIC_UNITS = {'temp_unit': '°C', 'precip_unit': 'mm', 'snow_unit': 'cm',
                'wind_unit': 'km/h', 'visibility_unit': 'km', 'pressure_unit': 'mb'}
UK_UNITS = {'temp_unit': '°C', 'precip_unit': 'mm', 'snow_unit': 'cm',
            'wind_unit': 'mph', 'visibility_unit': 'miles', 'pressure_unit': 'mb'}
US_UNITS = {'temp_unit': '°F', 'precip_unit': 'in', 'snow_unit': 'in',
            'wind_unit': 'mph', 'visibility_unit': 'miles', 'pressure_unit': 'mb'}

def home(request):
    context = {}
    if request.user.is_authenticated:
        UserPreferences.objects.filter(author=None, session=request.session.session_key).update(author=request.user)
        UserPreferences.objects.filter(author=request.user).exclude(session=request.session.session_key).delete()
        user_prefs, created = UserPreferences.objects.get_or_create(author=request.user,
            defaults={'units': 'us','author': request.user, 'session': request.session.session_key})
        units = user_prefs.units
        Location.objects.filter(session=request.session.session_key, author=None).update(author=request.user)
        duplicates = Location.objects.filter(author=request.user).values('loc').annotate(records=Count('loc')).filter(records__gt=1)
        if duplicates:
            Location.objects.filter(author=request.user, loc=duplicates[0]['loc']).exclude(session=request.session.session_key).delete()
        locations = list(Location.objects.filter(author=request.user).all().values())

        if units == 'metric':
            front_units = METRIC_UNITS
        elif units == 'uk':
            front_units = UK_UNITS 
        elif units == 'us':
            front_units = US_UNITS
        cards = {}
        for loc in locations:
            if units == 'us':
                loc['temp'] = round((float(loc['temp'])*1.8)+32, 1)
                loc['feelslike'] = round((float(loc['feelslike'])*1.8)+32, 1)
                loc['precip'] = round(float(loc['precip'])*25.4, 1)
                loc['snow'] = round(float(loc['snow'])*2.54, 1)
            cards[loc['loc']] = loc
        if not cards:
            context = {}
        else:
            context = {'saved_locs': cards, 'front_units': front_units}
    else:
        if not request.session.session_key:
            request.session.create()

        user_prefs, _ = UserPreferences.objects.get_or_create(session=request.session.session_key,
            defaults={'units': 'us', 'author': None, 'session': request.session.session_key})
        units = user_prefs.units
        request.session['units'] = user_prefs.units
        locations = list(Location.objects.filter(session=request.session.session_key).all().values())
        
        if units == 'metric':
            front_units = METRIC_UNITS
        elif units == 'uk':
            front_units = UK_UNITS
        elif units == 'us':
            front_units = US_UNITS
        cards = {}
        for loc in locations:
            if units == 'us':
                loc['temp'] = round((float(loc['temp'])*1.8)+32, 1)
                loc['feelslike'] = round((float(loc['feelslike'])*1.8)+32, 1)
                loc['precip'] = round(float(loc['precip'])*25.4, 1)
                loc['snow'] = round(float(loc['snow'])*2.54, 1)
            cards[loc['loc']] = loc

        context = {'saved_locs': cards, 'front_units': front_units}

    return render(request, 'fetch_weather/home.html', context)


def select_units(request):
    request_unit = request.GET.get('units')
    if request.user.is_authenticated:
        user_prefs, _ = UserPreferences.objects.get_or_create(author=request.user,
            defaults={'units': 'us', 'author': request.user, 'session': request.session.session_key})
        unit_from_db = UserPreferences.objects.filter(author=request.user).first()
        valid_units = {'metric': 'Metric', 'us': 'US', 'uk': 'UK'}
        if request_unit not in valid_units:
            return HttpResponseClientRefresh()
        locations = list(Location.objects.filter(author=request.user).all().values())
        
        if request_unit in valid_units:
            if request_unit == 'metric':
                units = METRIC_UNITS
                unit_from_db.units = 'metric'
            elif request_unit == 'uk':
                units = UK_UNITS
                unit_from_db.units = 'uk'
            elif request_unit == 'us':
                units = US_UNITS
                unit_from_db.units = 'us'
            unit_from_db.save()
            cards = {}
            for loc in locations:
                if request_unit == 'us':
                    loc['temp'] = round((float(loc['temp'])*1.8)+32, 1)
                    loc['feelslike'] = round((float(loc['feelslike'])*1.8)+32, 1)
                    loc['precip'] = round(float(loc['precip'])*25.4, 1)
                    loc['snow'] = round(float(loc['snow'])*2.54, 1)
                cards[loc['loc']] = loc
        else:
            context = {}
            units = {}
        context = {'saved_locs': cards, 'units': units}

    else:
        user_prefs, _ = UserPreferences.objects.get_or_create(session=request.session.session_key,
            defaults={'units': 'us', 'author': None,
            'session': request.session.session_key})
        unit_from_db = UserPreferences.objects.filter(session=request.session.session_key).first()
        valid_units = {'metric': 'Metric', 'us': 'US', 'uk': 'UK'}
        locations = list(Location.objects.filter(session=request.session.session_key).all().values())
        
        if request_unit in valid_units:
            cards = {}
            if request_unit == 'metric':
                units = METRIC_UNITS
                unit_from_db.units = 'metric'
            elif request_unit == 'uk':
                units = UK_UNITS
                unit_from_db.units = 'uk'
            elif request_unit == 'us':
                units = US_UNITS
                unit_from_db.units = 'us'
            unit_from_db.save()
            for loc in locations:
                if request_unit == 'us':
                    loc['temp'] = round((float(loc['temp'])*1.8)+32, 1)
                    loc['feelslike'] = round((float(loc['feelslike'])*1.8)+32, 1)
                    loc['precip'] = round(float(loc['precip'])*25.4, 1)
                    loc['snow'] = round(float(loc['snow'])*2.54, 1)
                cards[loc['loc']] = loc
        else:
            context = {}
        request.session['units'] = unit_from_db.units
        context = {'saved_locs': cards, 'units': units}
        
    return render(request, 'fetch_weather/partials/units.html', context)


def add_card(request):
    context = {}
    try:
        max_order_num = Location.objects.filter(author=request.user).last().order + 1
    except:
        max_order_num = 1
    
    location = request.POST.get('location')
    if location.isspace() or location == '':
        response = HttpResponse(status=204)
        response['HX-Trigger'] = json.dumps({'showMessage': [{"message": 'Please input a location.',
            "color": "bg-danger-subtle", "title": "Error"}]})
        return response
    geolocator = Nominatim(user_agent='http')
    location_validated = geolocator.geocode(location, addressdetails=True, language='en')
    if not location_validated:
        response = HttpResponse(status=204)
        response['HX-Trigger'] = json.dumps({'showMessage': [{"message": 'Please input a valid location.',
            "color": "bg-danger-subtle", "title": "Error"}]})
        return response

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
    elif state == '' and city == '':
        frontend_location = country
    else:
        frontend_location = ', '.join([city, state, country])

    url = (
        f'https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{frontend_location}'
        f'/next24hours?unitGroup=metric&elements=datetimeEpoch%2Clatitude%2Clongitude%2C'
        f'tempmax%2Ctempmin%2Ctemp%2Cfeelslikemax%2Cfeelslikemin%2Cfeelslike%2Chumidity%2Cprecip%2Cpreciptype%2C'
        f'snow%2Cpressure%2Ccloudcover%2Cuvindex%2Csunrise%2Csunset%2Cmoonphase%2Cconditions%2Cdescription%2Cicon'
        f'&iconSet=icons2&key={API_KEY}&contentType=json')
    
    weather_data = requests.get(url).json()
    cc = weather_data['currentConditions']

    if request.user.is_authenticated:
        if Location.objects.filter(loc=frontend_location, author=request.user).exists():
            response = HttpResponse(status=204)
            response['HX-Trigger'] = json.dumps({'showMessage': [{"message": f'{frontend_location} is already on your dashboard.',
            "color": "bg-danger-subtle", "title": "Error"}]})
            return response

        form_data = {'loc': frontend_location, 'datetimeEpoch': datetime.datetime.fromtimestamp(cc['datetimeEpoch'], tz=timezone.utc),
        'temp': cc['temp'], 'feelslike': cc['feelslike'],
        'humidity': cc['humidity'], 'precip': cc['precip'], 'snow': cc['snow'],
        'preciptype': cc['preciptype'], 'pressure': cc['pressure'], 'cloudcover': cc['cloudcover'],
        'uvindex': cc['uvindex'], 'conditions': cc['conditions'], 'icon': cc['icon'], 
        'sunrise': datetime.datetime.strftime(datetime.datetime.fromtimestamp(cc['datetimeEpoch'], tz=timezone.utc), "%Y-%m-%dT%H:%M:%SZ").split('T')[0] + 'T' + cc['sunrise'],
        'sunset': datetime.datetime.strftime(datetime.datetime.fromtimestamp(cc['datetimeEpoch'], tz=timezone.utc), "%Y-%m-%dT%H:%M:%SZ").split('T')[0] + 'T' + cc['sunset'],
        'moonphase': cc['moonphase'], 
        'daily_description': weather_data['description'], 'order': max_order_num, 'author': request.user,
        'session': request.session.session_key, 'tz_display_dt': datetime.datetime.strftime(datetime.datetime.fromtimestamp(cc['datetimeEpoch'], tz=timezone.utc), "%Y-%m-%dT%H:%M:%SZ"),
        'tz_display_lm': datetime.datetime.strftime(datetime.datetime.now(tz=timezone.utc), "%Y-%m-%dT%H:%M:%SZ"),
        'pretty_loc': re.sub("[, ]", '_', frontend_location)}
        form = LocationForm(form_data)
        if form.is_valid():
            form.save()

        user_prefs, _ = UserPreferences.objects.get_or_create(author=request.user,
        defaults={'units': 'us', 'author': request.user, 'session': request.session.session_key})
        units = user_prefs.units

        new_loc = Location.objects.filter(author=request.user).get(loc=frontend_location)     
    
    else:
        if Location.objects.filter(loc=frontend_location, session=request.session.session_key).exists():
            response = HttpResponse(status=204)
            response['HX-Trigger'] = json.dumps({'showMessage': [{"message": f'{frontend_location} is already on your dashboard.',
            "color": "bg-danger-subtle", "title": "Error"}]})
            return response
        
        form_data = {'loc': frontend_location, 'datetimeEpoch': datetime.datetime.fromtimestamp(cc['datetimeEpoch'], tz=timezone.utc),
        'temp': cc['temp'], 'feelslike': cc['feelslike'],
        'humidity': cc['humidity'], 'precip': cc['precip'], 'snow': cc['snow'],
        'preciptype': cc['preciptype'], 'pressure': cc['pressure'], 'cloudcover': cc['cloudcover'],
        'uvindex': cc['uvindex'], 'conditions': cc['conditions'], 'icon': cc['icon'], 
        'sunrise': datetime.datetime.strftime(datetime.datetime.fromtimestamp(cc['datetimeEpoch'], tz=timezone.utc), "%Y-%m-%dT%H:%M:%SZ").split('T')[0] + 'T' + cc['sunrise'],
        'sunset': datetime.datetime.strftime(datetime.datetime.fromtimestamp(cc['datetimeEpoch'], tz=timezone.utc), "%Y-%m-%dT%H:%M:%SZ").split('T')[0] + 'T' + cc['sunset'],
        'moonphase': cc['moonphase'], 
        'daily_description': weather_data['description'], 'order': max_order_num, 'author': None,
        'session': request.session.session_key, 'tz_display_dt': datetime.datetime.strftime(datetime.datetime.fromtimestamp(cc['datetimeEpoch'], tz=timezone.utc), "%Y-%m-%dT%H:%M:%SZ"),
        'tz_display_lm': datetime.datetime.strftime(datetime.datetime.now(tz=timezone.utc), "%Y-%m-%dT%H:%M:%SZ"),
        'pretty_loc': re.sub("[, ]", '_', frontend_location)}
        form = LocationForm(form_data)
        if form.is_valid():
            form.save()

        user_prefs, _ = UserPreferences.objects.get_or_create(session=request.session.session_key,
        defaults={'units': 'us', 'author': None, 'session': request.session.session_key})
        units = user_prefs.units
        request.session['units'] = user_prefs.units

        new_loc = Location.objects.filter(session=request.session.session_key).get(loc=frontend_location)     
        
    if units == 'metric':
        front_units = METRIC_UNITS
    elif units == 'uk':
        front_units = UK_UNITS
    elif units == 'us':
        front_units = US_UNITS
        new_loc.temp = round((float(new_loc.temp)*1.8)+32, 1)
        new_loc.feelslike = round((float(new_loc.feelslike)*1.8)+32, 1)
        new_loc.precip = round(float(new_loc.precip)*25.4, 1)
        new_loc.snow = round(float(new_loc.snow)*2.54, 1)
        
    context = {'new_card': new_loc, 'front_units': front_units}
        

    response = render(request, 'fetch_weather/partials/add_card.html', context)
    response['HX-Trigger'] = json.dumps({'showMessage': [{"message": f'{new_loc.loc} has been added to your dashboard.',
    "color": "bg-success-subtle", "title": "Added Location"}]})
    return response
        
    #eturn render(request, 'fetch_weather/home.html', context)

def remove_card(request):
    loc = request.POST
    new_loc = []
    for item in loc:
        new_loc.append(item)
    loc = ', '.join(new_loc)
    if request.user.is_authenticated:
        x = Location.objects.filter(author=request.user).get(loc=loc)
    else:
        x = Location.objects.filter(session=request.session.session_key).get(loc=loc)
    x.delete()
    context = {}
    response = render(request, 'fetch_weather/partials/remove_card.html', context)
    response['HX-Trigger'] = json.dumps({'showMessage': [{"message": f'{loc} has been removed from your dashboard.',
    "color": "bg-warning-subtle", "title": "Removed Location"}]})
    return response
    
def update_card(request):
    loc = request.POST
    new_loc = []
    for item in loc:
        new_loc.append(item)
    loc = ', '.join(new_loc)
    if request.user.is_authenticated:
        x = Location.objects.filter(author=request.user).get(loc=loc)
    else:
        x = Location.objects.filter(session=request.session.session_key).get(loc=loc)
    now = datetime.datetime.now(tz=timezone.utc)

    if (now - x.last_modified).seconds < 10:
        response = HttpResponse(status=204)
        response['HX-Trigger'] = json.dumps({'showMessage': [{"message": f'Please wait {round(30 - ((now-x.last_modified).seconds)/60)} minutes before manually refreshing {x.loc}.',
        "color": "bg-danger-subtle", "title": "Error"}]})
        return response
    
    url = (
        f'https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{x.loc}'
        f'/next24hours?unitGroup=metric&elements=datetime%2CdatetimeEpoch%2Clatitude%2Clongitude%2C'
        f'tempmax%2Ctempmin%2Ctemp%2Cfeelslikemax%2Cfeelslikemin%2Cfeelslike%2Chumidity%2Cprecip%2Cpreciptype%2C'
        f'snow%2Cpressure%2Ccloudcover%2Cuvindex%2Csunrise%2Csunset%2Cmoonphase%2Cconditions%2Cdescription%2Cicon'
        f'&iconSet=icons2&key={API_KEY}&contentType=json')
    weather_data = requests.get(url).json()
    cc = weather_data['currentConditions']
    x.datetimeEpoch = datetime.datetime.fromtimestamp(cc['datetimeEpoch'], tz=timezone.utc)
    x.temp = cc['temp']
    x.feelslike = cc['feelslike']
    x.humidity = cc['humidity']
    x.precip = cc['precip']
    x.snow = cc['snow']
    x.preciptype = cc['preciptype']
    x.pressure = cc['pressure']
    x.cloudcover = cc['cloudcover']
    x.uvindex = cc['uvindex']
    x.conditions = cc['conditions']
    x.icon = cc['icon']
    x.sunrise = datetime.datetime.strftime(datetime.datetime.fromtimestamp(cc['datetimeEpoch'], tz=timezone.utc), "%Y-%m-%dT%H:%M:%SZ").split('T')[0] + 'T' + cc['sunrise']
    x.sunset = datetime.datetime.strftime(datetime.datetime.fromtimestamp(cc['datetimeEpoch'], tz=timezone.utc), "%Y-%m-%dT%H:%M:%SZ").split('T')[0] + 'T' + cc['sunset']
    x.moonphase = cc['moonphase']
    x.daily_description = weather_data['description']
    x.last_modified = datetime.datetime.now(tz=timezone.utc)
    x.tz_display_lm = datetime.datetime.strftime(datetime.datetime.now(tz=timezone.utc), "%Y-%m-%dT%H:%M:%SZ")
    x.tz_display_dt = datetime.datetime.strftime(datetime.datetime.fromtimestamp(cc['datetimeEpoch'], tz=timezone.utc), "%Y-%m-%dT%H:%M:%SZ")
    x.save(update_fields=['datetimeEpoch', 'temp', 'feelslike', 'humidity',
    'precip', 'snow', 'preciptype', 'pressure', 'cloudcover', 'uvindex', 'conditions',
    'icon', 'sunrise', 'sunset', 'moonphase', 'daily_description', 'last_modified',
    'tz_display_lm', 'tz_display_dt'])
    #for x in range(len(weather_data['days'][0]['hours'])):
        #print(datetime.datetime.fromtimestamp(weather_data['days'][1]['hours'][x]['datetimeEpoch']))
    json_ob = json.dumps(weather_data, indent=4)
    with open('sample.json', 'w') as outfile:
        outfile.write(json_ob)

    if request.user.is_authenticated:
        x = Location.objects.filter(author=request.user).get(loc=loc)
        user_prefs, _ = UserPreferences.objects.get_or_create(author=request.user,
            defaults={'units': 'us', 'author': request.user, 'session': request.session.session_key})
    else:
        x = Location.objects.filter(session=request.session.session_key).get(loc=loc)
        user_prefs, _ = UserPreferences.objects.get_or_create(session=request.session.session_key,
            defaults={'units': 'us', 'author': None, 'session': request.session.session_key})
        
    units = user_prefs.units

    if units == 'metric':
        front_units = METRIC_UNITS
    elif units == 'uk':
        front_units = UK_UNITS
    elif units == 'us':
        front_units = US_UNITS
        x.temp = round((float(x.temp)*1.8)+32, 1)
        x.feelslike = round((float(x.feelslike)*1.8)+32, 1)
        x.precip = round(float(x.precip)*25.4, 1)
        x.snow = round(float(x.snow)*2.54, 1)

    context = {'new_card': x, 'front_units': front_units}

    response = render(request, 'fetch_weather/partials/update_card.html', context)
    response['HX-Trigger'] = json.dumps({'showMessage': [{"message": f'{x.loc} has been updated.',
    "color": "bg-info-subtle", "title": "Updated Location"}]})
    return response


def sort(request):
    if request.user.is_authenticated:
        locations = list(Location.objects.filter(author=request.user).all().values())
        user_prefs, _ = UserPreferences.objects.get_or_create(author=request.user,
            defaults={'units': 'us', 'author': request.user, 'session': request.session.session_key})
    else:
        locations = list(Location.objects.filter(session=request.session.session_key).all().values())
        user_prefs, _ = UserPreferences.objects.get_or_create(session=request.session.session_key,
            defaults={'units': 'us', 'author': None, 'session': request.session.session_key})
    card_order = dict(request.POST)
    card_order = card_order['card-order']
    units = user_prefs.units

    sorted_cards = {}
    cards = {}

    for loc in locations:
        if units == 'us':
            loc['temp'] = round((float(loc['temp'])*1.8)+32, 1)
            loc['feelslike'] = round((float(loc['feelslike'])*1.8)+32, 1)
            loc['precip'] = round(float(loc['precip'])*25.4, 1)
            loc['snow'] = round(float(loc['snow'])*2.54, 1)
        cards[loc['loc']] = loc

    for count, sorted_loc in enumerate(card_order):
        sorted_cards[sorted_loc] = cards[sorted_loc]
        if request.user.is_authenticated:
            loc1 = Location.objects.get(author=request.user, loc=sorted_loc)
            loc1.order = count + 1
            loc1.save(update_fields=['order'])
        else:
            loc1 = Location.objects.get(session=request.session.session_key, loc=sorted_loc)
            loc1.order = count + 1
            loc1.save(update_fields=['order'])

    if units == 'metric':
        front_units = METRIC_UNITS
    elif units == 'uk':
        front_units = UK_UNITS
    elif units == 'us':
        front_units = US_UNITS

    context = {'saved_locs': sorted_cards, 'front_units': front_units}
    return render(request, 'fetch_weather/partials/sort.html', context)


def about(request):
    return render(request, 'fetch_weather/about.html')


def past(request):
    return render(request, 'fetch_weather/past.html')

