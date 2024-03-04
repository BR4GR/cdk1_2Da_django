import plotly.express as px
import pandas as pd
from dash import dcc, html
from dash.dependencies import Input, Output
from django_plotly_dash import DjangoDash
from klimadaten.models import Station

EUROPE_NORTH = 71.5  # North Cape in Norway
EUROPE_SOUTH = 36  # Punta de Tarifa in Spain
EUROPE_WEST = -25  # Iceland
EUROPE_EAST = 60  # Ural Mountains in Russia

# Create a Dash app for displaying stations on a map
sapp = DjangoDash('StationsMap')

sapp.layout = html.Div([
    dcc.Dropdown(
        id='country-dropdown',
        options=list(Station.objects.values_list('country', flat=True).distinct().order_by('country')),
        value='ALL',
        clearable=False,
    ),
    dcc.Graph(id='stations-map'),
])


@sapp.callback(
    Output('stations-map', 'figure'),
    [Input('country-dropdown', 'value')]
)
def update_map(selected_country):
    df = fetch_station_data(selected_country)
    fig = px.scatter_mapbox(
        df,
        lat="lat",
        lon="lon",
        hover_name="name",
        hover_data=["elevation"],
        color_discrete_sequence=["fuchsia"],
        zoom=7,
        # height=300,
    )
    fig.update_layout(mapbox_style="open-street-map")
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    fig.update_layout(
        mapbox_bounds={"west": EUROPE_WEST, "east": EUROPE_EAST, "south": EUROPE_SOUTH,
                       "north": EUROPE_NORTH})
    return fig


def fetch_station_data(country=None):
    stations = Station.objects.all()
    if country and country != 'ALL':
        stations = stations.filter(country=country)

    # Create a DataFrame directly from the queryset
    df = pd.DataFrame.from_records(
        stations.values('name', 'lat', 'lon', 'elevation')
    )
    return df
