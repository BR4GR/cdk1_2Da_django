from django.core.management.base import BaseCommand, CommandError
import csv
from decimal import Decimal
from django.conf import settings
from klimadaten.models import Station
from itertools import islice

# Constants for Europe's geographic boundaries
EUROPE_NORTH = 71.5  # North Cape in Norway
EUROPE_SOUTH = 36  # Punta de Tarifa in Spain
EUROPE_WEST = -25  # Iceland
EUROPE_EAST = 60  # Ural Mountains in Russia


def dms_to_dd(dms):
    """Convert degrees:minutes:seconds to decimal degrees, accounting for hemisphere."""
    # Extract the sign (+ or -) from the start of the string
    sign = -1 if dms[0] == '-' else 1  # Assume + if no sign is explicitly given

    # Remove the sign from the string to avoid conversion issues
    dms = dms[1:] if dms[0] in '+-' else dms

    # Convert DMS to decimal degrees
    degrees, minutes, seconds = map(Decimal, dms.split(':'))
    return sign * (degrees + (minutes / 60) + (seconds / 3600))


def preprocess_country_name(row_string):
    # Replace problematic country names
    replacements = {
        "IRAN, ISLAMIC REPUBLIC OF": "ISLAMIC REPUBLIC OF IRAN",
        "TÃœRKIYE": "TURKIYE",
        "MOLDOVA, REPUBLIC OF": "REPUBLIC OF MOLDOVA",
    }
    for original, replacement in replacements.items():
        row_string = row_string.replace(original, replacement)
    return row_string


class Command(BaseCommand):
    help = 'Load data from CSV file into the database'

    def handle(self, *args, **kwargs):
        file_path = settings.BASE_DIR / 'klimadaten' / 'data' / 'stations_FXx.txt'
        try:
            with open(file_path, mode='r', encoding='utf-8') as csv_file:
                reader = csv.reader(islice(csv_file, 17, None))
                for row in reader:
                    try:
                        if row:  # Check if row is not empty
                            staid, name, country, lat, lon, elevation = row
                            # Convert DMS to decimal degrees
                            lat_dd = dms_to_dd(lat)
                            lon_dd = dms_to_dd(lon)

                            # Check if the station is within Europe's geographic boundaries
                            if (EUROPE_SOUTH <= lat_dd <= EUROPE_NORTH) and (EUROPE_WEST <= lon_dd <= EUROPE_EAST):
                                Station.objects.get_or_create(
                                    staid=int(staid.strip()),
                                    name=name.strip(),
                                    country=country.strip(),
                                    lat=lat_dd,
                                    lon=lon_dd,
                                    elevation=Decimal(elevation.strip())
                                )
                    except Exception as e:
                        # Print the error and current line for debugging
                        self.stdout.write(self.style.ERROR(f'Error processing line: {row}'))
                        self.stdout.write(self.style.ERROR(f'Error details: {e}'))
                        # Optionally, re-raise the exception if you want to stop execution
                        # raise e
        except FileNotFoundError:
            raise CommandError(f'The file {file_path} does not exist.')
