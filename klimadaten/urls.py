from django.urls import path
from . import views
from klimadaten.dash_apps.finished_apps import example
from klimadaten.dash_apps.finished_apps import stations_map

urlpatterns = [
    path('stations', views.stations, name='stations'),
    path('', views.map_stations, name='map_stations'),
    path('example', views.example, name='example'),
]
