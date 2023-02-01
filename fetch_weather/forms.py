from django.forms import ModelForm
from .models import Location

class LocationForm(ModelForm):
    class Meta:
        model = Location
        fields = ['loc', 'datetime', 'datetimeEpoch', 'temp', 'feelslike', 'humidity', 'precip',
        'snow', 'preciptype', 'pressure', 'cloudcover', 'uvindex', 'conditions', 'icon',
        'sunrise', 'sunset', 'moonphase', 'daily_description', 'order', 'author']

