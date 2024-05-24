from django.db import models


class Station(models.Model):
    staid = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    lat = models.DecimalField(max_digits=9, decimal_places=6)
    lon = models.DecimalField(max_digits=9, decimal_places=6)
    elevation = models.DecimalField(max_digits=9, decimal_places=2)

    def __str__(self):
        return f"{self.name} in {self.country}"


class City(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    iso2 = models.CharField(max_length=2)
    iso3 = models.CharField(max_length=3)
    lat = models.DecimalField(max_digits=9, decimal_places=6)
    lon = models.DecimalField(max_digits=9, decimal_places=6)

    def __str__(self):
        return f"{self.name} in {self.country}"


class Weather(models.Model):
    city = models.ForeignKey(
        City, on_delete=models.CASCADE, related_name="weather_data"
    )
    date = models.DateField()
    max_windspeed = models.DecimalField(
        max_digits=10, decimal_places=7, verbose_name="Wind Speed"
    )

    def __str__(self):
        return f"Weather data for {self.city.name} on {self.date}"

class Images(models.Model):
    title = models.CharField(max_length=255)
    image = models.ImageField(upload_to="images/")
    def __str__(self):
        return self.title