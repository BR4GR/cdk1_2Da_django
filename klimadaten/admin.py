from django.contrib import admin
from .models import Station, City, Weather

admin.site.register([Station, City, Weather])
