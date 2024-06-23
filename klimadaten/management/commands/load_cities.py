from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from klimadaten.models import City
import pandas as pd

# Constants for Europe's geographic boundaries
EUROPE_NORTH = 71.5  # North Cape in Norway
EUROPE_SOUTH = 36  # Punta de Tarifa in Spain
EUROPE_WEST = -25  # Iceland
EUROPE_EAST = 60  # Ural Mountains in Russia


class Command(BaseCommand):
    help = "Load data from CSV file into the database"

    def handle(self, *args, **kwargs):
        file_path = settings.BASE_DIR / "klimadaten" / "data" / "worldcities.csv"
        df = pd.read_csv(file_path)
        df_europe = df[
            (df["lat"] >= EUROPE_SOUTH)
            & (df["lat"] <= EUROPE_NORTH)
            & (df["lng"] >= EUROPE_WEST)
            & (df["lng"] <= EUROPE_EAST)
        ]

        for _, row in df_europe.iterrows():
            print(row["city"])
            City.objects.update_or_create(
                id=row["id"],
                defaults={
                    "name": row["city"],
                    "country": row["country"],
                    "iso2": row["iso2"],
                    "iso3": row["iso3"],
                    "lat": row["lat"],
                    "lon": row["lng"],
                },
            )

        self.stdout.write(
            self.style.SUCCESS("Successfully loaded European cities into the database.")
        )
