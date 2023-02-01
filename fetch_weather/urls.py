from django.urls import path
from . import views

urlpatterns = [
    path('about/', views.about, name='about'),
    path('history', views.past, name='history'),
    path('', views.home, name='home'),
    path('units/', views.select_units, name='units'),
    path('timezone/', views.select_timezone, name='timezone'),
    path('add_card/', views.add_card, name='add_card'),
    path('sort/', views.sort, name='sort'),
    path('remove_card/', views.remove_card, name='remove_card'),
]