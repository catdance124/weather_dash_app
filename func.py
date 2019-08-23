import pandas as pd
import numpy as np 
from datetime import datetime, timedelta
import os

tmp_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tmp")
if not os.path.exists(tmp_path):
    os.mkdir(tmp_path)


def get_csv(url='https://www.data.jma.go.jp/obd/stats/data/mdrr/pre_rct/alltable/pre1h00_rct.csv'):
    # 気象庁データ取得
    precip = pd.read_csv(url, encoding='shift-jis')
    if precip['現在時刻(時)'].unique()[0] == 24:
        precip['現在時刻(時)'] = precip['現在時刻(時)'] - 24
        precip['現在時刻(日)'] = precip['現在時刻(日)'] + 1
    precip['Date'] = precip[['現在時刻(年)', '現在時刻(月)', '現在時刻(日)', '現在時刻(時)', '現在時刻(分)']].\
                    apply(lambda x: '{}-{}-{} {:02}:{:02}'.format(x[0], x[1], x[2], x[3], x[4]), axis=1)
    precip.rename(columns={'観測所番号': '_id', '現在値(mm)':'precip'}, inplace=True)
    precip = precip[['_id', 'Date', 'precip']]
    precip = precip.dropna(subset=['precip'])
    # 観測点データを用意
    place_list = pd.read_csv('stations_info.csv', encoding='utf_8_sig')
    # 結合
    df = pd.merge(precip, place_list, how='left', on='_id')
    df['text'] = df[['name', 'precip']].apply(lambda x: '{}:  {}mm'.format(x[0], x[1]), axis=1)
    df.to_csv(os.path.join(tmp_path, 'latlon.csv'), encoding='utf_8_sig')
    return df

def check_file_time():
    df = pd.read_csv(os.path.join(tmp_path, 'latlon.csv'), encoding='utf_8_sig')
    file_time = datetime.strptime(str(df['Date'][0]), '%Y-%m-%d %H:%M')
    return file_time, df

def get_dataframe(recent_data=None, load=False):
    print('TRY UPDATE')
    file_time, df = check_file_time()
    now = datetime.utcnow() + timedelta(hours=9)
    if file_time < now - timedelta(minutes=30) and load:
        print('DO UPDATE')
        df = get_csv('https://www.data.jma.go.jp/obd/stats/data/mdrr/pre_rct/alltable/pre1h00_rct.csv')
        # df = get_csv('https://www.data.jma.go.jp/obd/stats/data/mdrr/pre_rct/alltable/pre1h00_rct.csv')
        # df = get_csv('https://www.data.jma.go.jp/obd/stats/data/mdrr/pre_rct/alltable/pre1h00_rct.csv')
        # df = get_csv('https://www.data.jma.go.jp/obd/stats/data/mdrr/pre_rct/alltable/pre1h00_rct.csv')
        recent_data =  get_recent_data()
    return df, recent_data

def get_recent_data():
    print('GET_____________RECENT  DATA')
    recent, _ = check_file_time()
    recent = recent.replace(minute=0)
    yesterday = recent - timedelta(days=1)
    i=0
    while yesterday <= recent:
        timestamp = yesterday.strftime('%Y%m%d%H%M')
        url = f'https://www.data.jma.go.jp/obd/stats/data/mdrr/pre_rct/alltable/pre1h00_{timestamp}.csv'
        df = get_csv(url)
        if i > 0:
            df_sum = pd.concat([df_sum, df])
        else:
            df_sum = df
        yesterday = yesterday + timedelta(minutes=30)
        i = i+1
    df_sum['Date'] = pd.to_datetime(df_sum['Date'])
    df_sum.sort_values(by='Date')
    df_sum.to_csv(os.path.join(tmp_path, 'df_24h.csv'), encoding='utf_8_sig')
    return df_sum

def get_colorscale():
    colorscale = []
    colorscale.append([0, f'rgb(230, 237, 230)'])
    colorscale.append([0.01, f'rgb(230, 237, 230)'])
    colorscale.append([0.01, f'rgb(150, 255, 255)'])
    colorscale.append([0.05, f'rgb(150, 255, 255)'])
    colorscale.append([0.05, f'rgb(0, 189, 255)'])
    colorscale.append([0.1, f'rgb(0, 189, 255)'])
    colorscale.append([0.1, f'rgb(0, 50, 255)'])
    colorscale.append([0.2, f'rgb(0, 50, 255)'])
    colorscale.append([0.2, f'rgb(255, 150, 0)'])
    colorscale.append([0.3, f'rgb(255, 150, 0)'])
    colorscale.append([0.3, f'rgb(255, 230, 0)'])
    colorscale.append([0.5, f'rgb(255, 230, 0)'])
    colorscale.append([0.5, f'rgb(255, 0, 0)'])
    colorscale.append([0.8, f'rgb(255, 0, 0)'])
    colorscale.append([0.8, f'rgb(141, 0, 22)'])
    colorscale.append([1.0, f'rgb(141, 0, 22)'])
    return colorscale