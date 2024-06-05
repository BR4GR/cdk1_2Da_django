from datetime import datetime
import pandas as pd
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings
from klimadaten.models import Images
from PIL import Image
import os


class Command(BaseCommand):
    help = "Load images from directory into the Images database model"

    def handle(self, *args, **options):
        image_dir = settings.BASE_DIR / "klimadaten" / "data" / "images"

        # Ensure the directory exists
        if not os.path.exists(image_dir):
            self.stdout.write(self.style.ERROR(f"Directory {image_dir} does not exist."))
            return

        # Loop over image files in the directory
        for image_file in os.listdir(image_dir):
            if image_file.lower().endswith(('png', 'jpg', 'jpeg', 'gif')):
                # Extract title from the image file name
                image_title = Path(image_file).stem

                try:
                    # Open image
                    image_path = image_dir / image_file
                    with Image.open(image_path) as img:
                        img.verify()  # Verify the image is valid

                    Images.objects.update_or_create(
                        title=image_title,
                        defaults={"image": str(image_path)}  # Konvertieren des Pfads in einen String
                    )

                    self.stdout.write(self.style.SUCCESS(f"Successfully loaded image: {image_title}."))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Failed to load image: {image_title}. Error: {e}"))

