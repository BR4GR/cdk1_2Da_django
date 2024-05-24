from django.contrib import admin
from .models import Station, City, Weather, Images

admin.site.register([Station, City, Weather, Images])
