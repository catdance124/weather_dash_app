# basic
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os, configparser, glob
import uuid
import pickle
# dash
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_daq as daq
import plotly.graph_objs as go
# original
from precip_colorscale import get_colorscale
from get_weather_data import load_new_data

# initial settings ===============================================================
external_stylesheets = ['http://catdance124.m24.coreserver.jp/dash/weather-app/assets/custom.css',
                        'https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)  #dash obj
server = app.server  #flask obj
app.config.update({
    'routes_pathname_prefix': '',
    'requests_pathname_prefix': ''
})
# sessions dir
os.makedirs('./sessions', exist_ok=True)
# global var
load_new_data()    # initial
recent_data = pd.read_pickle('./data/24h_precip.pkl')
latest_data = pd.read_pickle('./data/latest_precip.pkl')
# mapbox conf
config = configparser.ConfigParser()
config.read('./data/mapbox_access_token.conf')
mapbox_access_token = config.get('setting', 'token')
# title
app.title = 'Precipitation Map'

# layout ==========================================================================
def serve_layout():
    session_id = str(uuid.uuid4())
    return html.Div(
        children=[
            html.Div(session_id, id='session-id', style={'display': 'none'}),
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
                    style={'margin': '0px 10px 0px 0px', 'padding': '0px 10px',
                        'display': 'inline-block', 'vertical-align':'baseline'}
                ),
                html.Div([
                    html.Div(['multiple mode'], style={'font-size':'9pt'}),
                    daq.ToggleSwitch(id='force', value=False, size=35)
                ], style={'display': 'inline-block', 'vertical-align':'baseline'})
                ], style={'padding':'0px 0px 10px 0px'}
            ),
            html.Div(
                [dcc.Graph(id ='precipitation_24h')],
                style={'width':'80%', 'display': 'inline-block'}
            ),
            dcc.Interval(
                id='interval-component',
                interval=600*1000, # in milliseconds
                n_intervals=0
            ),
            html.Div(['© 2019 ', dcc.Link('kinosi', href='https://github.com/catdance124')],
                style={'padding':'20px 0px 0px 0px', 'font-size':'9pt'}
            ),
            dcc.Location(id='url', refresh=False),
            html.Div(id='update')
        ],
        style={'height':'100%', 'margin':'0', 'padding':'0', 'text-align': 'center'}
    )
app.layout = serve_layout()

# callbacks =======================================================================
@app.callback(Output('update', 'children'),
            [Input('interval-component', 'n_intervals')])
def load_data(n):
    global latest_data
    global recent_data
    recent_data = pd.read_pickle('./data/24h_precip.pkl')
    latest_data = pd.read_pickle('./data/latest_precip.pkl')
    for p in glob.glob("./sessions/*"):
        filetime = datetime.fromtimestamp(os.stat(p).st_mtime)
        theta = datetime.now() - timedelta(minutes=5)
        if filetime < theta:
            os.remove(p)

@app.callback(Output('update_time', 'children'),
            [Input('update', 'children')])
def print_time(n):
    file_update_time = datetime.fromtimestamp(os.stat('./data/latest_precip.pkl').st_mtime)
    file_update_time = file_update_time.strftime('%Y/%m/%d %H:%M:%S')
    return f'update time at  {file_update_time} (UTC+9)'

@app.callback(Output('data_time', 'children'),
            [Input('update', 'children')])
def print_time(n):
    t = datetime.strptime(str(latest_data['Date'][0]), '%Y-%m-%d %H:%M').strftime('%Y/%m/%d %H:%M:%S')
    return f'display info at {t} (UTC+9)'

@app.callback(Output('precipitation', 'figure'),
            [Input('update', 'children')])
def plot_precip(n):
    figure = {
        'data':[
            go.Scattermapbox(
            lat = latest_data['lat'],
            lon = latest_data['lon'],
            mode = 'markers',
            marker = dict(
                size=10,
                opacity=1,
                showscale=True,
                color=latest_data['precip'],
                cmin=0,
                cmax=100,
                colorscale=get_colorscale(),
                colorbar=dict(
                    tickmode="array",
                    tickvals=[0, 5, 10, 20, 30, 50, 80, 100],
                    title=dict(text='[mm/h]')
                )
            ),
            selected=dict(
                marker=dict(size=18)
            ),
            unselected=dict(
                marker=dict(opacity=0.9)
            ),
            text = latest_data['text'],
            customdata=latest_data['_id'],
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
                        lat = np.mean(latest_data['lat']),
                        lon = np.mean(latest_data['lon'])
                    ),
                    pitch = 0,
                    zoom = 3.8
                ),
                height = 370,
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
            [Input('precipitation', 'selectedData'),
            Input('session-id', 'children'),
            Input('force', 'value')])
def plot_precip_24h(selectedData, session_id, force):
    if selectedData is None:
        return dash.no_update
    else:
        selectedData = selectedData['points']
        store_data = {}
        if (len(selectedData) > 1 or force) and os.path.exists(f'./sessions/{session_id}.pkl'):
            f = open(f'./sessions/{session_id}.pkl','rb')
            store_data = pickle.load(f)
        for sd in selectedData:
            _id = sd['customdata']
            if _id not in store_data.keys():
                city = recent_data[recent_data['_id'] == _id]
                city_name = city['name'].unique()[0]
                store_data[_id] = go.Scatter(
                    x=city['Date'],
                    y=city['precip'],
                    mode='lines+markers',
                    name=city_name,
                    showlegend=True
                )
        f = open(f'./sessions/{session_id}.pkl','wb')
        pickle.dump(store_data,f)
        f.close
        figure = {
            'data': list(store_data.values()),
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
                    title='Hourly Precipitation (mm/h)'),
            )
        }
        return figure

@app.callback(Output('precipitation', 'selectedData'),
            [Input('reset_button','n_clicks')])
def reset(n):
    return {'points': [{'customdata': 44132}]}


if __name__=='__main__':
    app.run_server(debug=False)