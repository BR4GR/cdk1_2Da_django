from datetime import timedelta, datetime

from dash import dcc, html
from dash.dependencies import Input, Output, State
from django_plotly_dash import DjangoDash
from klimadaten.models import City
import plotly.express as px
import pandas as pd
import openmeteo_requests
import requests_cache
from retry_requests import retry

BEAUFORT_SCALE = {
    0: {'ms': 0, 'kmh': 0, 'name': "Windstille, Flaute"},
    1: {'ms': 0.3, 'kmh': 1, 'name': "Leiser Zug"},
    2: {'ms': 1.6, 'kmh': 6, 'name': "Leichte Brise"},
    3: {'ms': 3.4, 'kmh': 12, 'name': "Schwache Brise"},
    4: {'ms': 5.5, 'kmh': 20, 'name': "Mässige Brise"},
    5: {'ms': 8, 'kmh': 29, 'name': "Frische Brise"},
    6: {'ms': 10.8, 'kmh': 39, 'name': "Starker Wind"},
    7: {'ms': 13.9, 'kmh': 50, 'name': "Steifer Wind"},
    8: {'ms': 17.2, 'kmh': 62, 'name': "Stürmischer Wind"},
    9: {'ms': 20.8, 'kmh': 75, 'name': "Sturm"},
    10: {'ms': 24.5, 'kmh': 89, 'name': "Schwerer Sturm"},
    11: {'ms': 28.5, 'kmh': 103, 'name': "Orkanartiger Sturm"},
    12: {'ms': 32.7, 'kmh': 118, 'name': "Orkan"}
}

MONTH_NAMES = {
    '01': 'Januar',
    '02': 'Februar',
    '03': 'März',
    '04': 'April',
    '05': 'Mai',
    '06': 'Juni',
    '07': 'Juli',
    '08': 'August',
    '09': 'September',
    '10': 'Oktober',
    '11': 'November',
    '12': 'Dezember'
}

BLUES = {
    1: '#eff3ff',
    2: '#bdd7e7',
    3: '#6baed6',
    4: '#3182bd',
    5: '#08519c',
}  # https://colorbrewer2.org/#type=sequential&scheme=Blues&n=5

REDS = {
    1: '#fee5d9',
    2: '#fcae91',
    3: '#fb6a4a',
    4: '#de2d26',
    5: '#a50f15',
}  # https://colorbrewer2.org/#type=sequential&scheme=Reds&n=5

ORANGES = {
    1: '#feedde',
    2: '#fdbe85',
    3: '#fd8d3c',
    4: '#e6550d',
    5: '#a63603',
}  # https://colorbrewer2.org/#type=sequential&scheme=Oranges&n=5

PURD = {
    1: '#f1eef6',
    2: '#d7b5d8',
    3: '#df65b0',
    4: '#dd1c77',
    5: '#980043',
}  # https://colorbrewer2.org/#type=sequential&scheme=PuRd&n=5
CHOSEN = PURD
STATION_COLOR = CHOSEN[4]
CITY_COLOR = CHOSEN[5]
SECONDARY_COLOR = CHOSEN[2]
BACKGROUND_COLOR = CHOSEN[1]

EUROPE_NORTH = 71.5  # North Cape in Norway
EUROPE_SOUTH = 36  # Punta de Tarifa in Spain
EUROPE_WEST = -25  # Iceland
EUROPE_EAST = 60  # Ural Mountains in Russia

# Create a Dash app for displaying stations on a map
app = DjangoDash("StationsMap")


def fetch_data():
    station_data = City.objects.all()
    df = pd.DataFrame.from_records(station_data.values("name", "lat", "lon", "country", "iso2"))
    return df


# Initial data fetch
station_data = fetch_data().to_dict('records')

# Initial selected station data
initial_selected_station = {
    "name": "Sumba",
    "lat": 61.405500,
    "lon": -6.709000,
    "country": "Faroe Islands",
    "iso2": "FO",
}

app.layout = html.Div(
    [
        dcc.Store(id='station-data', data=station_data),
        dcc.Store(id='selected-station-data', data=initial_selected_station),
        html.Div(id="selected-station"),
        html.Div(
            [
                dcc.Graph(id="station-map", style={"width": "70%", "display": "inline-block"}),
                html.Div(
                    [
                        html.H2(),
                        html.Label('Windgeschwindigkeit:'),
                        dcc.Dropdown(
                            id='windspeed-dropdown',
                            options=[{'label': f"{scale['name']} ({scale['kmh']} km/h)", 'value': scale['kmh']} for
                                     scale in BEAUFORT_SCALE.values()],
                            value=75,
                        ),
                        html.H3('für Vergleich und Langzeitanalyse'),
                        html.Label('Auswahl der zweiten Ortschaft zum Vergleich:'),
                        dcc.Dropdown(
                            id='city-dropdown',
                            options=[{'label': f"{city.name}, {city.country}", 'value': city.id} for city in
                                     City.objects.all()],
                            value=1756121125,  # Default value Brugg
                        ),
                        html.Label('Jahr das verglichen werden soll:'),
                        dcc.Dropdown(
                            id='year-dropdown',
                            options=[{'label': str(year), 'value': year} for year in range(1940, 2025)],
                            value=1991,
                        ),
                        html.Label('Monat:'),
                        dcc.Dropdown(
                            id='month-dropdown',
                            options=[
                                {'label': 'Januar', 'value': '01'},
                                {'label': 'Februar', 'value': '02'},
                                {'label': 'März', 'value': '03'},
                                {'label': 'April', 'value': '04'},
                                {'label': 'Mai', 'value': '05'},
                                {'label': 'Juni', 'value': '06'},
                                {'label': 'Juli', 'value': '07'},
                                {'label': 'August', 'value': '08'},
                                {'label': 'September', 'value': '09'},
                                {'label': 'Oktober', 'value': '10'},
                                {'label': 'November', 'value': '11'},
                                {'label': 'Dezember', 'value': '12'}
                            ],
                            value='04',
                        ),

                    ],
                    style={"width": "25%", "display": "inline-block", "verticalAlign": "top", "padding": "20px"}
                ),
            ]
        ),
        html.Div(
            [
                html.H2("Das letzte Jahr", style={'textAlign': 'center', 'margin-top': '70px'}),
                # html.P(
                #     "Willkommen zur Klimadaten Challenge! Auf der interaktiven Karte können Sie Wetterstationen "
                #     "europaweit erkunden und die Windgeschwindigkeiten an verschiedenen Orten visualisieren. "
                #     "Klicken Sie auf einen Punkt der Karte, um die höchsten täglichen Windgeschwindigkeiten "
                #     "des letzten Jahres am gewählten Standort zu betrachten. Unterhalb der Karte finden Sie zwei "
                #     "detaillierte Analysen: Eine Liniendiagramm-Darstellung der täglichen Windgeschwindigkeiten und "
                #     "ein Balkendiagramm, das die Anzahl der Tage pro Monat mit Windgeschwindigkeiten über 25 km/h "
                #     "zeigt. Diese Einblicke ermöglichen es Ihnen, Windmuster zu vergleichen und die Variabilität der "
                #     "Windverhältnisse über einen Zeitraum von einem Jahr zu untersuchen.",
                #     style={'margin': '20px'}
                # )
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
                html.H2("Langzeitvergleich und Saison", style={'textAlign': 'center'}),
                # html.P(
                #     "Der untere Abschnitt der Anwendung ermöglicht es den Benutzern, historische Winddaten "
                #     "tiefergehend zu analysieren. Im linken Diagramm wird der Vergleich der Windgeschwindigkeiten "
                #     "zwischen zwei Standorten über das ausgewählte Jahr dargestellt. Dies erlaubt eine direkte "
                #     "Gegenüberstellung der Windbedingungen und zeigt auf, wie unterschiedlich das Wetter in "
                #     "verschiedenen Regionen sein kann. Das rechte Balkendiagramm erweitert diese Analyse auf mehrere "
                #     "Jahrzehnte und zeigt die Anzahl der Tage im Januar, an denen die Windgeschwindigkeit 25 km/h "
                #     "überschritten hat. Durch diese Langzeitdarstellung können Nutzerinnen und Nutzer Veränderungen "
                #     "und Muster im Windverhalten über die Jahre erkennen, was für Klimaforschung und langfristige "
                #     "Wettervorhersagen von Bedeutung sein kann.",
                #     style={'margin': '20px'}
                # )
            ]
        ),

        html.Div(
            [
                dcc.Graph(id="yearly-comparison-plot", style={"width": "50%", "display": "inline-block"}),
                dcc.Graph(id="monthly-comparison-plot", style={"width": "50%", "display": "inline-block"})
            ]
        )
    ]
)


@app.callback(
    [Output("station-map", "figure"), Output("selected-station", "children")],
    [Input("station-map", "clickData")],
    [State("station-data", "data"), State("selected-station-data", "data")]
)
def update_map(clickData, station_data, selected_station):
    df = pd.DataFrame(station_data)
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

    if clickData:
        selected_station["name"] = clickData["points"][0]["hovertext"]
        selected_station["lat"] = clickData["points"][0]["lat"]
        selected_station["lon"] = clickData["points"][0]["lon"]
        selected_station["country"] = clickData["points"][0]["customdata"][0]
        selected_station["iso2"] = clickData["points"][0]["customdata"][1]

    fig_map.update_layout(
        mapbox=dict(
            center=dict(
                lat=int(selected_station["lat"]), lon=int(selected_station["lon"])
            ),  # Center the map on Europe
            zoom=4,
        )
    )
    return fig_map, selected_station


@app.callback(
    [Output("wind-speed-lineplot", "figure"), Output("wind-speed-barplot", "figure")],
    [Input("selected-station", "children"), Input('windspeed-dropdown', 'value')],
)
def update_plots(selected_station, selected_windspeed):
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
    fig_lineplot.update_layout(
        plot_bgcolor=BACKGROUND_COLOR,
        # paper_bgcolor=BACKGROUND_COLOR  # Slightly different shade of light grey
    )

    # daily_dataframe['date'] = pd.to_datetime(daily_dataframe['date'])

    # Filter data for wind speed > selected_windspeed and count days
    over_selected_windspeed = last_year[last_year["wind_speed_10m_max"] > selected_windspeed]
    start = over_selected_windspeed["date"].min()
    end = over_selected_windspeed["date"].max()
    # Creating a complete range of months
    all_months = pd.date_range(
        start=start_date, end=end_date, freq="MS"
    ).to_period("M")

    # Counting days over selected windspeed by month
    over_selected_windspeed["month"] = over_selected_windspeed["date"].dt.to_period("M")
    monthly_counts = (
        over_selected_windspeed.groupby("month")
        .size()
        .reindex(all_months, fill_value=0)
        .reset_index(name="days_over_selected_windspeed")
    )

    # Converting the 'month' period to datetime for plotting
    monthly_counts["month"] = monthly_counts["index"].dt.to_timestamp()

    # Bar plot for days per month with wind speed over selected windspeed
    fig_barplot = px.bar(
        monthly_counts,
        x="month",
        y="days_over_selected_windspeed",
        range_y=[0, 31],
        title=f"Tage pro Monat mit Windgeschwindigkeiten über {selected_windspeed} km/h im letzten Jahr",
        labels={"days_over_selected_windspeed": f"Tage über {selected_windspeed} km/h", "month": "Monat"},
        color_discrete_sequence=[STATION_COLOR],
    )

    return fig_lineplot, fig_barplot


@app.callback(
    Output('yearly-comparison-plot', 'figure'),
    [Input('city-dropdown', 'value'),
     Input('year-dropdown', 'value'),
     Input("selected-station", "children")]
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


@app.callback(
    Output('monthly-comparison-plot', 'figure'),
    [Input('city-dropdown', 'value'),
     Input('month-dropdown', 'value'),
     Input("selected-station", "children"),
     Input('windspeed-dropdown', 'value')]
)
def update_monthly_comparison_plot(city_id, month, selected_station, selected_windspeed):
    current_year = datetime.now().year
    years = range(1940, current_year)

    city_days_over_selected_windspeed = []
    station_days_over_selected_windspeed = []

    dropdown_city = City.objects.get(id=city_id)

    for year in years:
        start_date = f"{year}-04-01"
        end_date = f"{year}-04-31"
        if isinstance(month, str):
            start_date = f"{year}-{month}-01"
            end_date = f"{year}-{month}-31"

        city_data = call_open_meteo({
            'lat': dropdown_city.lat,
            'lon': dropdown_city.lon
        }, start_date, end_date)

        station_data = call_open_meteo({
            'lat': selected_station['lat'],
            'lon': selected_station['lon']
        }, start_date, end_date)

        # Filter data for wind speed > selected_windspeed and count days
        city_days_count = city_data[city_data['wind_speed_10m_max'] > selected_windspeed].shape[0]
        station_days_count = station_data[station_data['wind_speed_10m_max'] > selected_windspeed].shape[0]

        city_days_over_selected_windspeed.append(city_days_count)
        station_days_over_selected_windspeed.append(station_days_count)
        station_label = f"{selected_station['name']} ({selected_station['iso2']})"
        city_label = f"{dropdown_city.name} ({dropdown_city.iso2})"

    # Create a DataFrame for plotting
    comparison_df = pd.DataFrame({
        'Jahre': list(years),
        station_label: station_days_over_selected_windspeed,
        city_label: city_days_over_selected_windspeed
    })

    month_name = MONTH_NAMES.get(month, "Monat")

    fig = px.bar(
        comparison_df,
        x='Jahre',
        y=[station_label, city_label],
        barmode='group',
        title=f'Tage mit über {selected_windspeed} km/h im {month_name} seit 1940',
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
