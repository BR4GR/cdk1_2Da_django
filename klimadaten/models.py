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

    class Meta:
        ordering = ['name']