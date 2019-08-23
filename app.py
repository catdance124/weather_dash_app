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
app.title = 'Precipitation Map'
server = app.server # for Heroku

# init download
_ = get_csv()  # get latest data
recent_data = get_recent_data()  # get recent 24h data

# layout
app.layout = html.Div(
    children=[
        html.H1(children="Precipitation Map",style={'margin-bottom':'10px'}),
        html.Div(id="update_time"),
        html.Div(id="data_time"),
        html.Br(),
        html.Div(
            [dcc.Graph(id ='precipitation', selectedData={'points': [{'customdata': 44132}]})],
            style={'width':'80%', 'display': 'inline-block'}
        ),
        html.Div(
            [html.Button('select reset',id='reset_button', n_clicks=0,
                style={'position':'absolute','right':'20%', 'padding':0})],
            style={'padding':'0px 0px 30px 0px'}
        ),
        html.Div(
            [dcc.Graph(id ='precipitation_24h')],
            style={'width':'80%', 'display': 'inline-block'}
        ),
        dcc.Interval(
            id='interval-component',
            interval=300*1000, # in milliseconds
            n_intervals=0
        ),
        html.Div(id="loader")
    ],
    style={'height':'100%', 'margin':'0', 'padding':'0', 'text-align': 'center'}
)

@app.callback(Output('update_time', 'children'),
            [Input('interval-component', 'n_intervals')])
def print_time(n):
    DIFF_JST_FROM_UTC = 9
    now = datetime.utcnow() + timedelta(hours=DIFF_JST_FROM_UTC)
    now = now.strftime('%Y/%m/%d %H:%M:%S')
    return f'update time at  {now} (UTC+9)'

@app.callback(Output('data_time', 'children'),
            [Input('interval-component', 'n_intervals')])
def print_time(n):
    df, _ = get_dataframe(recent_data=None, load=False)
    t = datetime.strptime(str(df['Date'][0]), '%Y-%m-%d %H:%M').strftime('%Y/%m/%d %H:%M:%S')
    return f'display info at {t} (UTC+9)'

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
                colorbar=dict(
                    tickmode="array",
                    tickvals=[0, 5, 10, 20, 30, 50, 80, 100],
                )
            ),
            unselected=dict(
                marker=dict(opacity=0.3)
            ),
            text = df['text'],
            customdata=df['_id'],
            )
        ],
        'layout':
            go.Layout(
                title=dict(
                    text='Click: Select | Shift+Click: Multiple select',
                    font={'size':15}
                ),
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
                    zoom = 3.8
                ),
                height = 400,
                paper_bgcolor='rgb(0,0,0,0)',
                margin = dict(
                    l = 0, r = 0, t = 30, b = 0,
                    autoexpand = True
                ),
                clickmode = 'event+select'
            )
    }
    return figure

@app.callback(Output('precipitation_24h', 'figure'),
            [Input('precipitation', 'selectedData')])
def plot_precip_24h(selectedData):
    if selectedData is None:
        return dash.no_update
    else:
        selectedData = selectedData['points']
        data = []
        for sd in selectedData:
            _id = sd['customdata']
            city = recent_data[recent_data['_id'] == _id]
            city_name = city['name'].unique()[0]
            data.append(go.Scatter(
                x=city['Date'],
                y=city['precip'],
                mode='lines+markers',
                name=city_name,
                showlegend=True
            ))
        figure = {
            'data': data,
            'layout': dict(
                title=dict(
                    text=f'24 hrs precipitation',
                    yref='container',
                    y=0.96
                ),
                height=360,
                paper_bgcolor='rgb(0,0,0,0)',
                plot_bgcolor='rgb(250,250,250)',
                legend=dict(
                    bgcolor='rgb(250,250,250)',
                ),
                margin=dict(
                    l = 50, r = 50, t = 40, b = 60,
                    autoexpand = True
                ),
                xaxis=dict(
                    showgrid=False,
                    title='Datetime'),
                yaxis=dict(
                    showgrid=True,
                    title='Temperature (degree celsius)'),
            )
        }
        return figure

@app.callback(Output('precipitation', 'selectedData'),
            [Input('reset_button','n_clicks')])
def update(reset):
    return {'points': [{'customdata': 44132}]}


@app.callback(Output('loader', 'children'),
            [Input('interval-component', 'n_intervals')])
def print_time(n):
    get_dataframe(recent_data=None, load=False)


if __name__=='__main__':
    app.run_server(debug=False, port=5000)