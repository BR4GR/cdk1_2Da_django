from django.shortcuts import render
from django.db.models import Count
from klimadaten.models import Station
from plotly.offline import plot
from .forms import CountryForm
import plotly.express as px
import plotly.graph_objects as go


def example(request):
    return render(request, "klimadaten/example.html")


def map_stations(request):
    return render(request, 'klimadaten/map_stations.html')


def stations(request):
    barplot = country_count_bar()
    context = {'barplot': barplot}
    return render(
        request,
        'klimadaten/stations.html',
        context
    )


def country_count_bar():
    stations_per_country = Station.objects.values('country').annotate(total=Count('country')).order_by('-total')
    countries = stations_per_country.values_list('country', flat=True)
    total = stations_per_country.values_list('total', flat=True)
    fig = px.bar(
        x=stations_per_country.values_list('country', flat=True),
        y=stations_per_country.values_list('total', flat=True),
        title='Number of Stations per Country',
        labels={'x': 'Country', 'y': 'Number of Stations'},
    )
    fig.update_layout(
        title={
            'font_size': 28,
            'xanchor': 'center',
            'x': 0.5,
        }
    )
    return fig.to_html()
