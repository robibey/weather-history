from django import forms

class LocationForm(forms.Form):
    city = forms.TextInput()