from django.forms import ModelForm
from .models import Location

class LocationForm(ModelForm):
    class Meta:
        model = Location
        fields = ['loc', 'datetimeEpoch', 'temp', 'feelslike', 'humidity', 'precip',
        'snow', 'preciptype', 'pressure', 'cloudcover', 'uvindex', 'conditions', 'icon',
        'sunrise', 'sunset', 'moonphase', 'daily_description', 'order', 'author', 'session',
        'tz_display_dt', 'tz_display_lm', 'pretty_loc']

