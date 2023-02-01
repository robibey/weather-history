from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class UserPreferencesForm(forms.ModelForm):
    units = forms.CharField(max_length=6)
    timezone = forms.CharField(max_length=32)

    class Meta:
        model = User
        fields = ['units']