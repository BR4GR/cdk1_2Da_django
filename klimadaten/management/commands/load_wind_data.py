from datetime import datetime
import pandas as pd
from scipy.spatial import cKDTree
from django.core.management.base import BaseCommand
from django.conf import settings
from klimadaten.models import City, Weather
from pathlib import Path


class Command(BaseCommand):
    help = 'Load wind speed data from CSV files into the database'

    def handle(self, *args, **options):
        file_path = settings.BASE_DIR / 'klimadaten' / 'data' / 'wws19791205.csv'
        # Extract year and month from the file name
        # Extract the date from the filename
        date_str = Path(file_path).stem[3:]  # Assuming format 'wwsYYYYMMDD'
        date = datetime.strptime(date_str, '%Y%m%d').date()

        # Read wind speed data
        df_wind = pd.read_csv(file_path)

        # Prepare data for nearest neighbor search
        cities = City.objects.all().values_list('id', 'lat', 'lon')
        df_cities = pd.DataFrame(cities, columns=['id', 'lat', 'lon'])
        city_coords = list(zip(df_cities['lat'], df_cities['lon']))
        wind_coords = list(zip(df_wind['lat'], df_wind['lon']))

        # Find nearest city for each wind data point
        tree = cKDTree(city_coords)
        distances, indices = tree.query(wind_coords, k=1)

        # Load data into the database
        for idx, city_idx in enumerate(indices):
            city_id = df_cities.iloc[city_idx]['id']
            city = City.objects.get(id=city_id)
            Weather.objects.update_or_create(
                city=city,
                date=date,
                defaults={'max_windspeed': df_wind.iloc[idx]['FX']}
            )

        self.stdout.write(self.style.SUCCESS(f'Successfully loaded wind data for {date}.'))
