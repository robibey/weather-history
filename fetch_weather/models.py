from django.db import models
from django.contrib.auth.models import User
from django.db.models import Max

class Location(models.Model):
    loc = models.CharField(max_length=60)
    datetime = models.TimeField()
    datetimeEpoch = models.IntegerField()
    temp = models.FloatField()
    feelslike = models.FloatField()
    humidity = models.FloatField()
    precip = models.FloatField()
    snow = models.FloatField()
    preciptype = models.CharField(max_length=50, null=True, blank=True)
    pressure = models.FloatField()
    cloudcover = models.FloatField()
    uvindex = models.FloatField()
    conditions = models.CharField(max_length=50)
    icon = models.CharField(max_length=30)
    sunrise = models.TimeField()
    sunset = models.TimeField()
    moonphase = models.FloatField()
    daily_description = models.CharField(max_length=150)
    last_modified = models.TimeField(auto_now=True)
    order = models.SmallIntegerField()
    author = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        unique_together = ['loc', 'author']
        ordering = ['order']