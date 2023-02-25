from django.db import models
from django.contrib.auth.models import User
from django.db.models.constraints import UniqueConstraint

class Location(models.Model):
    loc = models.CharField(max_length=100)
    datetimeEpoch = models.DateTimeField()
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
    sunrise = models.CharField(max_length=30)
    sunset = models.CharField(max_length=30)
    moonphase = models.FloatField()
    daily_description = models.TextField()
    last_modified = models.DateTimeField(auto_now=True)
    order = models.SmallIntegerField()
    author = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session = models.TextField()
    tz_display_dt = models.CharField(max_length=30)
    tz_display_lm = models.CharField(max_length=30)
    pretty_loc = models.CharField(max_length=100)

    class Meta:
        unique_together = ['loc', 'author', 'session']
        ordering = ['order']