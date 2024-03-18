from django.shortcuts import render
from django.db.models import Count
from klimadaten.models import Station, City
import plotly.express as px
import pandas as pd


EUROPE_NORTH = 71.5  # North Cape in Norway
EUROPE_SOUTH = 36  # Punta de Tarifa in Spain
EUROPE_WEST = -25  # Iceland
EUROPE_EAST = 60  # Ural Mountains in Russia


def example(request):
    return render(request, "klimadaten/example.html")


def map_stations(request):
    return render(request, "klimadaten/map_stations.html")


def stations(request):
    barplot = country_count_bar()
    map = get_map()
    context = {"barplot": barplot, "map": map}
    return render(request, "klimadaten/stations.html", context)


def country_count_bar():
    stations_per_country = (
        City.objects.values("country")
        .annotate(total=Count("country"))
        .order_by("-total")
    )
    fig = px.bar(
        x=stations_per_country.values_list("country", flat=True),
        y=stations_per_country.values_list("total", flat=True),
        title="Number of Stations per Country",
        labels={"x": "Country", "y": "Number of Stations"},
    )
    fig.update_layout(
        title={
            "font_size": 28,
            "xanchor": "center",
            "x": 0.5,
        }
    )
    return fig.to_html()


def get_map():
    df = fetch_station_data()
    fig = px.scatter_mapbox(
        df,
        lat="lat",
        lon="lon",
        hover_name="name",
        # hover_data=["elevation"],
        # color_continuous_scale=px.colors.sequential.Turbo,
        zoom=7,
        # height=300,
    )
    fig.update_layout(mapbox_style="open-street-map")
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    fig.update_layout(
        mapbox_bounds={
            "west": EUROPE_WEST,
            "east": EUROPE_EAST,
            "south": EUROPE_SOUTH,
            "north": EUROPE_NORTH,
        }
    )
    return fig.to_html()


def fetch_station_data(country=None):
    station_data = City.objects.all()
    if country and country != "ALL":
        station_data = station_data.filter(country=country)

    # Create a DataFrame directly from the queryset
    df = pd.DataFrame.from_records(
        # station_data.values('name', 'lat', 'lon', 'elevation')
        station_data.values("name", "lat", "lon")
    )
    return df
