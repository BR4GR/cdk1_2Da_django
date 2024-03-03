from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
from django_plotly_dash import DjangoDash
from klimadaten.models import Station

# Create a Dash app for displaying stations on a map
sapp = DjangoDash('StationsMap')


# Assuming you have a function to fetch stations data based on a selected country
def fetch_station_data(country=None):
    stations = Station.objects.all()
    if country and country != 'ALL':
        stations = stations.filter(country=country)
    lats = [station.lat for station in stations]
    lons = [station.lon for station in stations]
    names = [station.name for station in stations]
    # Add more data extraction as necessary
    return lats, lons, names


sapp.layout = html.Div([
    dcc.Dropdown(
        id='country-dropdown',
        options=[{'label': country, 'value': country} for country in
                 Station.objects.values_list('country', flat=True).distinct()],
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
    lats, lons, names = fetch_station_data(selected_country)
    fig = go.Figure(data=go.Scattergeo(
        lon=lons,
        lat=lats,
        text=names,
        mode='markers',
        marker=dict(size=8, color="blue", line=dict(width=1, color='rgba(102, 102, 102)')),
    ))
    fig.update_layout(geo=dict(scope='europe'))
    return fig
