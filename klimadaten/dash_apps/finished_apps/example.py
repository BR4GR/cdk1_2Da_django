from dash import dcc, html
from dash.dependencies import Input, Output
from django_plotly_dash import DjangoDash
from django.conf import settings
import plotly.express as px
import pandas as pd


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

file_path = settings.BASE_DIR / 'klimadaten' / 'data' / 'wws19791205.csv'
data = pd.read_csv(file_path)
df = pd.DataFrame(data)
df = df[df['FX'] > 25]

app = DjangoDash('SimpleExample', external_stylesheets=external_stylesheets)

app.layout = html.Div([
    dcc.Graph(id='wind-map'),
    dcc.Dropdown(
        id='year-picker',
        options=[{'label': year, 'value': year} for year in range(2000, 2023)],  # Example year range
        value=2022,  # Default value
    ),
    dcc.Dropdown(
        id='month-picker',
        options=[{'label': month, 'value': month} for month in range(1, 13)],  # Months 1-12
        value=1,  # Default value
    )
])


# Callback to update the map based on year and month pickers
@app.callback(
    Output('wind-map', 'figure'),
    [Input('year-picker', 'value'),
     Input('month-picker', 'value')]
)
def update_map(selected_year, selected_month):
    # For now, we ignore the year and month in the data filtering
    # You would add filtering logic here based on the selected year and month
    fig = px.scatter_geo(df,
                         lat='lat',
                         lon='lon',
                         color='FX',
                         hover_name='FX',
                         projection='natural earth',
                         title='Wind Speeds over Europe')
    fig.update_geos(
        visible=False,
        projection_type='equirectangular',
        fitbounds="locations",
        showcountries=True,
        countrycolor="RebeccaPurple"
    )
    return fig


if __name__ == '__main__':
    ...
