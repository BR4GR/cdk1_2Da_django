from dash import dcc, html
from dash.dependencies import Input, Output
from django_plotly_dash import DjangoDash
from klimadaten.models import City
import plotly.express as px
import pandas as pd
import numpy as np
import openmeteo_requests
import requests_cache
from retry_requests import retry

EUROPE_NORTH = 71.5  # North Cape in Norway
EUROPE_SOUTH = 36  # Punta de Tarifa in Spain
EUROPE_WEST = -25  # Iceland
EUROPE_EAST = 60  # Ural Mountains in Russia
MIN_DATE = "1940-01-01"
MAX_DATE = "2024-02-29"

# Create a Dash app for displaying stations on a map
sapp = DjangoDash("StationsMap")

sapp.layout = html.Div(
    [
        html.Div(id="selected-station"),
        dcc.Graph(id="station-map"),
        html.Div(
            [
                dcc.Graph(id="wind-speed-lineplot", style={"width": "50%", "display": "inline-block"}),
                dcc.Graph(id="wind-speed-barplot", style={"width": "50%", "display": "inline-block"}),
            ],
        ),
    ]
)


@sapp.callback(
    Output("station-map", "figure"),
    Output("selected-station", "children"),
    [Input("station-map", "clickData")],  # Triggered by clicking on the map
)
def update_map(clickData):
    df = fetch_data()
    fig_map = px.scatter_mapbox(
        df,
        lat="lat",
        lon="lon",
        hover_name="name",
        hover_data=["country"],
        zoom=6,
        mapbox_style="open-street-map",
    )
    fig_map.update_layout(coloraxis_colorbar_title_text="Max Wind Speed (km/h)")
    fig_map.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    selected_station = {
        "name": "Namsos",
        "lat": 64.4656,
        "lon": 11.4978,
        "country": "Norway",
    }
    if clickData:
        selected_station["name"] = clickData["points"][0]["hovertext"]
        selected_station["lat"] = clickData["points"][0]["lat"]
        selected_station["lon"] = clickData["points"][0]["lon"]
        selected_station["country"] = clickData["points"][0]["customdata"][0]
    fig_map.update_layout(
        mapbox=dict(
            center=dict(
                lat=int(selected_station["lat"]), lon=int(selected_station["lon"])
            ),  # Center the map on Europe
            zoom=4,
        )
    )
    return fig_map, selected_station


def fetch_data():
    station_data = City.objects.all()
    df = pd.DataFrame.from_records(station_data.values("name", "lat", "lon", "country"))
    return df


@sapp.callback(
    [Output("wind-speed-lineplot", "figure"), Output("wind-speed-barplot", "figure")],
    [Input("selected-station", "children")],
)
def update_plots(selected_station):
    daily_dataframe = call_open_meteo(selected_station)

    # last_year = daily_dataframe['date'].max().year
    last_year = daily_dataframe[daily_dataframe["date"].dt.year >= 2023]
    # Line plot for daily max wind speed
    fig_lineplot = px.line(
        last_year,
        x="date",
        y="wind_speed_10m_max",
        title=f"Höchste Windgeschwindigkeit pro Tag in {selected_station['name']}, {selected_station['country']}",
        labels={
            "wind_speed_10m_max": "Maximale Windgeschwindigkeit (km/h)",
            "date": "Datum",
        },
    )

    # daily_dataframe['date'] = pd.to_datetime(daily_dataframe['date'])

    over_25 = last_year[last_year["wind_speed_10m_max"] > 25]
    start = over_25["date"].min()
    end = over_25["date"].max()
    # Creating a complete range of months
    all_months = pd.date_range(
        start="2023-02-01", end="2024-02-29", freq="MS"
    ).to_period("M")

    # Counting days over 25 km/h by month
    over_25["month"] = over_25["date"].dt.to_period("M")
    monthly_counts = (
        over_25.groupby("month")
        .size()
        .reindex(all_months, fill_value=0)
        .reset_index(name="days_over_25")
    )

    # Converting the 'month' period to datetime for plotting
    monthly_counts["month"] = monthly_counts["index"].dt.to_timestamp()

    # Bar plot for days per month with wind speed over 25
    fig_barplot = px.bar(
        monthly_counts,
        x="month",
        y="days_over_25",
        title=f"Tage pro Monat mit Windgeschwindigkeiten über 25 km/h",
        labels={"days_over_25": "Tage über 25 km/h", "month": "Monat"},
    )

    return fig_lineplot, fig_barplot


def call_open_meteo(selected_station):
    # Setup the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession(".cache", expire_after=-1)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    # The order of variables in hourly or daily is important to assign them correctly below
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": selected_station["lat"],
        "longitude": selected_station["lon"],
        "start_date": MIN_DATE,
        "end_date": MAX_DATE,
        "daily": "wind_speed_10m_max",
        "timezone": "Europe/Berlin",
    }
    responses = openmeteo.weather_api(url, params=params)

    # Process first location. Add a for-loop for multiple locations or weather models
    response = responses[0]

    # Process daily data. The order of variables needs to be the same as requested.
    daily = response.Daily()
    daily_wind_speed_10m_max = daily.Variables(0).ValuesAsNumpy()

    daily_data = {
        "date": pd.date_range(
            start=pd.to_datetime(daily.Time(), unit="s", utc=True),
            end=pd.to_datetime(daily.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=daily.Interval()),
            inclusive="left",
        ),
        "wind_speed_10m_max": daily_wind_speed_10m_max,
    }

    daily_dataframe = pd.DataFrame(data=daily_data)
    return daily_dataframe
