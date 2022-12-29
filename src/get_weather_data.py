import pandas as pd
import numpy as np 
from datetime import datetime, timedelta
import os

def get_jma_data(url, data_type='precip', latest=True):
    if data_type == 'precip':
        column = '現在値(mm)'
    # 気象庁データ取得
    jma = pd.read_csv(url, encoding='shift-jis')
    if jma['現在時刻(時)'].unique()[0] == 24:
        jma['現在時刻(時)'] = jma['現在時刻(時)'] - 24
        jma['現在時刻(日)'] = jma['現在時刻(日)'] + 1
    jma['Date'] = jma[['現在時刻(年)', '現在時刻(月)', '現在時刻(日)', '現在時刻(時)', '現在時刻(分)']].\
                    apply(lambda x: '{}-{}-{} {:02}:{:02}'.format(x[0], x[1], x[2], x[3], x[4]), axis=1)
    jma.rename(columns={'観測所番号': '_id', column:data_type}, inplace=True)
    jma = jma[['_id', 'Date', data_type]]
    jma = jma.dropna(subset=[data_type])
    # 観測点データ読み込み
    place_list = pd.read_csv('../data/stations_info.csv', encoding='utf_8_sig')
    # 結合
    df = pd.merge(jma, place_list, how='left', on='_id')
    df['text'] = df[['name', data_type]].apply(lambda x: '{}:  {}mm'.format(x[0], x[1]), axis=1)
    if latest:        
        df.to_pickle(f'../data/latest_{data_type}.pkl')
    else:
        return df


def get_24h_data(data_type='precip'):
    latest_df = pd.read_pickle(f'../data/latest_{data_type}.pkl')
    latest_time = datetime.strptime(str(latest_df['Date'][0]), '%Y-%m-%d %H:%M')
    if 0 <= latest_time.minute < 30:
        latest_time = latest_time.replace(minute=0)
    else:
        latest_time = latest_time.replace(minute=30)
    prev_time = latest_time - timedelta(days=1)

    df_24h = None
    if os.path.exists(f'../data/24h_{data_type}.pkl'):    # update prev_time
        df_24h = pd.read_pickle(f'../data/24h_{data_type}.pkl')
        df_24h['Date'] = pd.to_datetime(df_24h['Date'])
        df_24h = df_24h[df_24h['Date'] >= prev_time]  # delete old data
        if len(df_24h) != 0:
            prev_time = datetime.strptime(str(df_24h['Date'][len(df_24h)-1]), '%Y-%m-%d %H:%M:%S')  # latest date
    while prev_time <= latest_time:
        timestamp = prev_time.strftime('%Y%m%d%H%M')
        if data_type == 'precip':
            url = f'https://www.data.jma.go.jp/obd/stats/data/mdrr/pre_rct/alltable/pre1h00_{timestamp}.csv'
        df = get_jma_data(url, data_type=data_type, latest=False)
        if df_24h is None:
            df_24h = df
        else:
            df_24h = pd.concat([df_24h, df])
        prev_time = prev_time + timedelta(minutes=30)
    df_24h['Date'] = pd.to_datetime(df_24h['Date'])
    df_24h.sort_values(by='Date')
    df_24h = df_24h.drop_duplicates()
    df_24h.reset_index(inplace=True, drop=True)
    df_24h.to_pickle(f'../data/24h_{data_type}.pkl')

def load_new_data():
    file_update_time = datetime.now() - timedelta(days=3)
    if os.path.exists(f'../data/latest_precip.pkl'):
        file_update_time = datetime.fromtimestamp(os.stat('../data/latest_precip.pkl').st_mtime)
    if file_update_time < datetime.now() - timedelta(minutes=2):
        get_jma_data('https://www.data.jma.go.jp/obd/stats/data/mdrr/pre_rct/alltable/pre1h00_rct.csv', data_type='precip')
        get_24h_data(data_type='precip')


if __name__ == '__main__':
    load_new_data()
