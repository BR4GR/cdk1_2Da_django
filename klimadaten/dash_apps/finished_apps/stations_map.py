from datetime import timedelta, datetime

from dash import dcc, html
from dash.dependencies import Input, Output
from django_plotly_dash import DjangoDash
from klimadaten.models import City
import plotly.express as px
import pandas as pd
import openmeteo_requests
import requests_cache
from retry_requests import retry

STATION_COLOR = "orange"
CITY_COLOR = "red"
SECONDARY_COLOR = "grey"
EUROPE_NORTH = 71.5  # North Cape in Norway
EUROPE_SOUTH = 36  # Punta de Tarifa in Spain
EUROPE_WEST = -25  # Iceland
EUROPE_EAST = 60  # Ural Mountains in Russia

# Create a Dash app for displaying stations on a map
sapp = DjangoDash("StationsMap")

sapp.layout = html.Div(
    [
        html.Div(id="selected-station"),
        dcc.Graph(id="station-map"),
        html.Div(
            [
                html.H2("Klimadaten Challenge", style={'textAlign': 'center', 'margin-top': '70px'}),
                html.P(
                    "Willkommen zur Klimadaten Challenge! Auf der interaktiven Karte können Sie Wetterstationen "
                    "europaweit erkunden und die Windgeschwindigkeiten an verschiedenen Orten visualisieren. "
                    "Klicken Sie auf einen Punkt der Karte, um die höchsten täglichen Windgeschwindigkeiten "
                    "des letzten Jahres am gewählten Standort zu betrachten. Unterhalb der Karte finden Sie zwei "
                    "detaillierte Analysen: Eine Liniendiagramm-Darstellung der täglichen Windgeschwindigkeiten und "
                    "ein Balkendiagramm, das die Anzahl der Tage pro Monat mit Windgeschwindigkeiten über 25 km/h "
                    "zeigt. Diese Einblicke ermöglichen es Ihnen, Windmuster zu vergleichen und die Variabilität der "
                    "Windverhältnisse über einen Zeitraum von einem Jahr zu untersuchen.",
                    style={'margin': '20px'}
                )
            ]
        ),
        html.Div(
            [
                dcc.Graph(id="wind-speed-lineplot", style={"width": "50%", "display": "inline-block"}),
                dcc.Graph(id="wind-speed-barplot", style={"width": "50%", "display": "inline-block"}),
            ],
        ),
        html.Div(
            [
                html.H2("Langzeitvergleich und Jahresanalyse", style={'textAlign': 'center'}),
                html.P(
                    "Der untere Abschnitt der Anwendung ermöglicht es den Benutzern, historische Winddaten "
                    "tiefergehend zu analysieren. Im linken Diagramm wird der Vergleich der Windgeschwindigkeiten "
                    "zwischen zwei Standorten über das ausgewählte Jahr dargestellt. Dies erlaubt eine direkte "
                    "Gegenüberstellung der Windbedingungen und zeigt auf, wie unterschiedlich das Wetter in "
                    "verschiedenen Regionen sein kann. Das rechte Balkendiagramm erweitert diese Analyse auf mehrere "
                    "Jahrzehnte und zeigt die Anzahl der Tage im Januar, an denen die Windgeschwindigkeit 25 km/h "
                    "überschritten hat. Durch diese Langzeitdarstellung können Nutzerinnen und Nutzer Veränderungen "
                    "und Muster im Windverhalten über die Jahre erkennen, was für Klimaforschung und langfristige "
                    "Wettervorhersagen von Bedeutung sein kann.",
                    style={'margin': '20px'}
                )
            ]
        ),
        html.Div(
            [
                dcc.Dropdown(
                    id='city-dropdown',
                    options=[{'label': f"{city.name}, {city.country}", 'value': city.id} for city in City.objects.all()],
                    value=1756121125,  # Default value Brugg
                    style={'width': '30%', 'display': 'inline-block'}
                ),
                dcc.Dropdown(
                    id='year-dropdown',
                    options=[{'label': str(year), 'value': year} for year in range(1940, 2025)],
                    value=1991,  # Default value
                    style={'width': '30%', 'display': 'inline-block', 'margin-left': '1%'}
                ),
                dcc.Dropdown(
                    id='month-dropdown',
                    options=[
                        {'label': 'Januar', 'value': 1},
                        {'label': 'Februar', 'value': 2},
                        {'label': 'März', 'value': 3},
                        {'label': 'April', 'value': 4},
                        {'label': 'Mai', 'value': 5},
                        {'label': 'Juni', 'value': 6},
                        {'label': 'Juli', 'value': 7},
                        {'label': 'August', 'value': 8},
                        {'label': 'September', 'value': 9},
                        {'label': 'Oktober', 'value': 10},
                        {'label': 'November', 'value': 11},
                        {'label': 'Dezember', 'value': 12}
                    ],
                    value=4,  # Default value for April
                    style={'width': '30%', 'display': 'inline-block', 'margin-left': '1%'}
                )
            ], style={'padding': '20px'}
        ),
        html.Div(
            [
                dcc.Graph(id="yearly-comparison-plot", style={"width": "50%", "display": "inline-block"}),
                dcc.Graph(id="monthly-comparison-plot", style={"width": "50%", "display": "inline-block"})
            ]
        )
    ]
)


@sapp.callback(
    Output("station-map", "figure"),
    Output("selected-station", "children"),
    [Input("station-map", "clickData")],
)
def update_map(clickData):
    df = fetch_data()
    fig_map = px.scatter_mapbox(
        df,
        lat="lat",
        lon="lon",
        hover_name="name",
        hover_data=["country", "iso2"],
        zoom=5,
        mapbox_style="open-street-map",
        color_discrete_sequence=[SECONDARY_COLOR],
    )
    fig_map.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    selected_station = {
        "name": "Sumba",
        "lat": 61.405500,
        "lon": -6.709000,
        "country": "Faroe Islands",
        "iso2": "FO",
    }

    if clickData:
        selected_station["name"] = clickData["points"][0]["hovertext"]
        selected_station["lat"] = clickData["points"][0]["lat"]
        selected_station["lon"] = clickData["points"][0]["lon"]
        selected_station["country"] = clickData["points"][0]["customdata"][0]
        selected_station["iso2"] = clickData["points"][0]["customdata"][1]

    fig_map.add_scattermapbox(
        lat=[selected_station["lat"]],
        lon=[selected_station["lon"]],
        mode='markers',
        marker=dict(size=10, color=STATION_COLOR),
        name="Selected Station"
    )

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
    df = pd.DataFrame.from_records(station_data.values("name", "lat", "lon", "country", "iso2"))
    return df


@sapp.callback(
    [Output("wind-speed-lineplot", "figure"), Output("wind-speed-barplot", "figure")],
    [Input("selected-station", "children")],
)
def update_plots(selected_station):
    today = pd.Timestamp.now().normalize()  # Get current date without time
    start_date = (today - timedelta(days=365 + 10)).strftime('%Y-%m-%d')  # One year and 10 days ago
    end_date = (today - timedelta(days=10)).strftime('%Y-%m-%d')  # 10 days ago
    daily_dataframe = call_open_meteo(selected_station, start_date, end_date)

    # last_year = daily_dataframe['date'].max().year
    last_year = daily_dataframe[daily_dataframe["date"].dt.year >= 2023]
    # Line plot for daily max wind speed
    fig_lineplot = px.line(
        last_year,
        x="date",
        y="wind_speed_10m_max",
        title=f"Höchste Windgeschwindigkeit pro Tag in {selected_station['name']}, {selected_station['country']} im letzten Jahr",
        labels={
            "wind_speed_10m_max": "Maximale Windgeschwindigkeit (km/h)",
            "date": "Datum",
        },
    )
    fig_lineplot.update_traces(line=dict(color=STATION_COLOR))

    # daily_dataframe['date'] = pd.to_datetime(daily_dataframe['date'])

    over_25 = last_year[last_year["wind_speed_10m_max"] > 25]
    start = over_25["date"].min()
    end = over_25["date"].max()
    # Creating a complete range of months
    all_months = pd.date_range(
        start=start_date, end=end_date, freq="MS"
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
        range_y=[0, 31],
        title=f"Tage pro Monat mit Windgeschwindigkeiten über 25 km/h im letzten Jahr",
        labels={"days_over_25": "Tage über 25 km/h", "month": "Monat"},
        color_discrete_sequence=[STATION_COLOR],
    )

    return fig_lineplot, fig_barplot


@sapp.callback(
    Output('yearly-comparison-plot', 'figure'),
    [Input('city-dropdown', 'value'), Input('year-dropdown', 'value'), Input("selected-station", "children")]
)
def update_yearly_comparison_plot(city_id, year, selected_station):
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"
    current_year = datetime.now().year
    if year == current_year:
        today = pd.Timestamp.now().normalize()
        start_date = (today - timedelta(days=365 + 10)).strftime('%Y-%m-%d')
        end_date = (today - timedelta(days=10)).strftime('%Y-%m-%d')

    city = City.objects.get(id=city_id)

    city_data = call_open_meteo({
        'lat': city.lat,
        'lon': city.lon
    }, start_date, end_date)

    station_data = call_open_meteo(selected_station, start_date, end_date)
    station_label = f"{selected_station['name']} ({selected_station['iso2']})"
    city_label = f"{city.name} ({city.iso2})"

    # Combine data and create plot
    fig = px.line(
        pd.concat([station_data.assign(Ortschaft=station_label), city_data.assign(Ortschaft=city_label)]),
        x='date',
        y='wind_speed_10m_max',
        color='Ortschaft',
        labels={'wind_speed_10m_max': 'Windgeschwindigkeit', 'date': 'Jahr'},
        color_discrete_map={station_label: STATION_COLOR, city_label: CITY_COLOR},
        title=f"Vergleich der Windgeschwindigkeiten von {station_label} und {city_label} im Jahr {year}"
    )
    return fig


@sapp.callback(
    Output('monthly-comparison-plot', 'figure'),
    [Input('city-dropdown', 'value'), Input('month-dropdown', 'value'), Input("selected-station", "children")]
)
def update_monthly_comparison_plot(city_id, month, selected_station):
    current_year = datetime.now().year
    years = range(current_year - 34, current_year + 1)  # Last 35 years

    city_days_over_25 = []
    station_days_over_25 = []

    dropdown_city = City.objects.get(id=city_id)

    for year in years:
        start_date = f"{year}-01-01"
        end_date = f"{year}-01-31"

        city_data = call_open_meteo({
            'lat': dropdown_city.lat,
            'lon': dropdown_city.lon
        }, start_date, end_date)

        station_data = call_open_meteo({
            'lat': selected_station['lat'],
            'lon': selected_station['lon']
        }, start_date, end_date)

        # Filter data for wind speed > 25 and count days
        city_days_count = city_data[city_data['wind_speed_10m_max'] > 25].shape[0]
        station_days_count = station_data[station_data['wind_speed_10m_max'] > 25].shape[0]

        city_days_over_25.append(city_days_count)
        station_days_over_25.append(station_days_count)
        station_label = f"{selected_station['name']} ({selected_station['iso2']})"
        city_label = f"{dropdown_city.name} ({dropdown_city.iso2})"

    # Create a DataFrame for plotting
    comparison_df = pd.DataFrame({
        'Jahre': list(years),
        station_label: station_days_over_25,
        city_label: city_days_over_25
    })

    fig = px.bar(
        comparison_df,
        x='Jahre',
        y=[station_label, city_label],
        barmode='group',
        title='Aprill Tage mit über 25km/h für augewählte Ortschaften in den letzten 35 Jahren',
        labels={'value': 'Anzahl Tage', 'variable': 'Ortschaft'},
        color_discrete_map={station_label: STATION_COLOR, city_label: CITY_COLOR},
    )

    return fig


def call_open_meteo(selected_station, start_date, end_date):
    # Setup the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession(".cache", expire_after=-1)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    # The order of variables in hourly or daily is important to assign them correctly below
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": selected_station["lat"],
        "longitude": selected_station["lon"],
        "start_date": start_date,
        "end_date": end_date,
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
