import pandas as pd
import numpy as np 
import dash 
import dash_core_components as dcc
import dash_html_components as html 
from dash.dependencies import Input, Output
import plotly.graph_objs as go
from datetime import datetime, timedelta
import os, configparser


config = configparser.ConfigParser()
config.read('mapbox_access_token.conf')
mapbox_access_token = config.get('setting', 'token')
app = dash.Dash(__name__)
server = app.server # for Heroku

app.layout = html.Div(children=[
    html.H1(children="Precipitation Map"),
    html.Div(id="now_time"),
    dcc.Graph(id = 'precipitation'),
    dcc.Interval(
        id='interval-component',
        interval=600*1000, # in milliseconds
        n_intervals=0
    )
])

def get_csv(url):
    # 気象庁データ取得
    precip = pd.read_csv(url, encoding='shift-jis')
    precip['Date'] = precip[['現在時刻(年)', '現在時刻(月)', '現在時刻(日)', '現在時刻(時)', '現在時刻(分)']].\
                    apply(lambda x: '{}-{}-{} {}:{}'.format(x[0], x[1], x[2], x[3], x[4]), axis=1)
    precip.rename(columns={'観測所番号': '_id', '現在値(mm)':'precip'}, inplace=True)
    precip = precip[['_id', 'Date', 'precip']]
    precip = precip.dropna(subset=['precip'])
    # 観測点データを用意
    place_list = pd.read_csv('stations_info.csv', encoding='utf_8_sig')
    # 結合
    df = pd.merge(precip, place_list, how='left', on='_id')
    df['text'] = df[['name', 'precip']].apply(lambda x: '{}:  {}mm'.format(x[0], x[1]), axis=1)
    df.to_csv('latlon.csv', encoding='utf_8_sig')
    return df

def get_dataframe():
    df = pd.read_csv('latlon.csv', index_col=0)
    file_time = datetime.strptime(str(df['Date'][0]), '%Y-%m-%d %H:%M')
    if file_time < datetime.now() - timedelta(minutes=30):
        df = get_csv('https://www.data.jma.go.jp/obd/stats/data/mdrr/pre_rct/alltable/pre1h00_rct.csv')
        # df = get_csv('https://www.data.jma.go.jp/obd/stats/data/mdrr/pre_rct/alltable/pre1h00_rct.csv')
        # df = get_csv('https://www.data.jma.go.jp/obd/stats/data/mdrr/pre_rct/alltable/pre1h00_rct.csv')
        # df = get_csv('https://www.data.jma.go.jp/obd/stats/data/mdrr/pre_rct/alltable/pre1h00_rct.csv')
    return df

def get_colorscale():
    colorscale = []
    colorscale.append([0, f'rgb(230, 237, 230)'])
    colorscale.append([0.01, f'rgb(230, 237, 230)'])##
    colorscale.append([0.01, f'rgb(150, 255, 255)'])
    colorscale.append([0.05, f'rgb(150, 255, 255)'])##
    colorscale.append([0.05, f'rgb(0, 189, 255)'])
    colorscale.append([0.1, f'rgb(0, 189, 255)'])##
    colorscale.append([0.1, f'rgb(0, 50, 255)'])
    colorscale.append([0.2, f'rgb(0, 50, 255)'])##
    colorscale.append([0.2, f'rgb(255, 150, 0)'])
    colorscale.append([0.3, f'rgb(255, 150, 0)'])##
    colorscale.append([0.3, f'rgb(255, 230, 0)'])
    colorscale.append([0.5, f'rgb(255, 230, 0)'])##
    colorscale.append([0.5, f'rgb(255, 0, 0)'])
    colorscale.append([0.8, f'rgb(255, 0, 0)'])##
    colorscale.append([0.8, f'rgb(141, 0, 22)'])
    colorscale.append([1.0, f'rgb(141, 0, 22)'])##
    return colorscale

@app.callback(Output('now_time', 'children'),
            [Input('interval-component', 'n_intervals')])
def print_time(n):
    df = get_dataframe()
    t = datetime.strptime(str(df['Date'][0]), '%Y-%m-%d %H:%M').strftime('%Y/%m/%d %H:%M')
    return t + 'の降水情報'

@app.callback(Output('precipitation', 'figure'),
            [Input('interval-component', 'n_intervals')])
def plot_precip(n):
    df = get_dataframe()
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
            )
        ],
        'layout':
            go.Layout(
                autosize=True,
                hovermode='closest',
                mapbox = dict(
                    accesstoken=mapbox_access_token,
                    bearing = 0,
                    center = dict(
                        lat=np.mean(df['lat']),
                        lon=np.mean(df['lon'])
                    ),
                    pitch=0,
                    zoom=4.2
                ),
                height=900
            )
    }
    return figure


if __name__=='__main__':
    app.run_server(debug=True)