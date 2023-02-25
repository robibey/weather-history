from django.db import models
from django.contrib.auth.models import User

class UserPreferences(models.Model):
    units = models.CharField(max_length=10, default='us')
    author = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session = models.TextField()
