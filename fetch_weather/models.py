from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

units = (('Celsius', 'Celsius'), ('Fahrenheit', 'Fahrenheit'))


#@login_required
class Location(models.Model):
    units = models.CharField(max_length=10, choices=units, default='Celsius')
    locs = models.TextField(max_length=500)
    datetime = models.DateTimeField(default=timezone.now)
    author = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.locs