import pandas as pd
import numpy as np 
import dash 
import dash_core_components as dcc
import dash_html_components as html 
from dash.dependencies import Input, Output
import plotly.graph_objs as go
from datetime import datetime, timedelta
import os, configparser
from func import get_dataframe, get_colorscale, get_recent_data, get_csv

config = configparser.ConfigParser()
config.read('mapbox_access_token.conf')
mapbox_access_token = config.get('setting', 'token')
app = dash.Dash(__name__)
app.title = 'My Title'
server = app.server # for Heroku

# init download
_ = get_csv()  # get latest data
recent_data = get_recent_data()  # get recent 24h data

# layout
app.layout = html.Div(
    children=[
        html.H1(children="Precipitation Map"),
        html.Div(id="update_time"),
        html.Div(id="data_time"),
        html.Div(
            [dcc.Graph(id ='precipitation', clickData={'points': [{'customdata': 44132}]})],
            style={'width': '39%', 'display': 'inline-block'}
        ),
        html.Div(
            [dcc.Graph(id ='precipitation_24h')],
            style={'width': '59%', 'display': 'inline-block', 'float': 'right'}
        ),
        dcc.Interval(
            id='interval-component',
            interval=300*1000, # in milliseconds
            n_intervals=0
        ),
        html.Div(id="loader")
    ]
)

@app.callback(Output('update_time', 'children'),
            [Input('interval-component', 'n_intervals')])
def print_time(n):
    DIFF_JST_FROM_UTC = 9
    now = datetime.utcnow() + timedelta(hours=DIFF_JST_FROM_UTC)
    now = now.strftime('%Y/%m/%d %H:%M:%S')
    return f'update time: {now}'

@app.callback(Output('data_time', 'children'),
            [Input('interval-component', 'n_intervals')])
def print_time(n):
    df, _ = get_dataframe(recent_data=None, load=False)
    t = datetime.strptime(str(df['Date'][0]), '%Y-%m-%d %H:%M').strftime('%Y/%m/%d %H:%M')
    return f'{t}の降水情報'

@app.callback(Output('precipitation', 'figure'),
            [Input('interval-component', 'n_intervals')])
def plot_precip(n):
    global recent_data
    df, recent_data = get_dataframe(recent_data, load=False)
    figure = {
        'data':[
            go.Scattermapbox(
            lat = df['lat'],
            lon = df['lon'],
            mode = 'markers',
            marker = dict(
                size=10,
                opacity=1,
                showscale=True,
                color=df['precip'],
                cmin=0,
                cmax=100,
                colorscale=get_colorscale(),
            ),
            text = df['text'],
            customdata=df['_id'],
            )
        ],
        'layout':
            go.Layout(
                autosize = True,
                hovermode = 'closest',
                mapbox = dict(
                    accesstoken = mapbox_access_token,
                    bearing = 0,
                    center = dict(
                        lat = np.mean(df['lat']),
                        lon = np.mean(df['lon'])
                    ),
                    pitch = 0,
                    zoom = 4.2
                ),
                height = 800,
                margin = dict(
                    l = 0, r = 0, t = 0, b = 0,
                    autoexpand = True
                ),
                clickmode = 'event'
            )
    }
    return figure

@app.callback(Output('precipitation_24h', 'figure'),
            [Input('precipitation', 'clickData')])
def plot_precip_24h(clickData):
    if clickData is None:
        return dash.no_update
    else:
        _id = clickData['points'][0]['customdata']
        city = recent_data[recent_data['_id'] == _id]
        city_name = city['name'].unique()[0]
        figure = {
            'data': [
                go.Scatter(
                x=city['Date'],
                y=city['precip'],
                mode='lines+markers',
            )],
            'layout': dict(
                title=f'Temperature {city_name}',
                height=350,
                paper_bgcolor='rgb(245,245,245)',
                plot_bgcolor='rgb(245,245,245)',
                margin=dict(
                    l = 50, r = 50, t = 50, b = 60,
                    autoexpand = True
                ),
                xaxis=dict(
                    showgrid=False,
                    title='Date'),
                yaxis=dict(
                    showgrid=True,
                    title='Temperature (degree celsius)'),
            )
        }
        return figure

@app.callback(Output('loader', 'children'),
            [Input('interval-component', 'n_intervals')])
def print_time(n):
    get_dataframe(recent_data=None, load=True)


if __name__=='__main__':
    app.run_server(debug=True, port=5000)