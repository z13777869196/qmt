import numpy as np
import pandas as pd
cb_data = pd.read_parquet('C:/Users/robert/PycharmProjects/stockStrategy/backtest/data/cb_data.pq')
cb_data.reset_index(inplace=True)
print(cb_data.columns)
def add_return(group_data):
    if group_data['next_day_open'] >= group_data['close'] * 1.03:
        group_data['next_day_return_stop_win3'] =(group_data['next_day_open'] - group_data['close']) / group_data['close']
    elif group_data['next_day_high']>=group_data['close']*1.03:
        group_data['next_day_return_stop_win3'] = 0.03
    else:
        group_data['next_day_return_stop_win3'] = group_data['next_day_return']
    if group_data['next_day_open']  >= group_data['close'] * 1.06:
        group_data['next_day_return_stop_win6'] =(group_data['next_day_open']  - group_data['close']) / group_data['close']
    elif group_data['next_day_high']>=group_data['close']*1.06:
        group_data['next_day_return_stop_win6'] = 0.06
    else:
        group_data['next_day_return_stop_win6'] = group_data['next_day_return']
    return group_data
add_return_pd = None
for code, group_data in cb_data.groupby('code'):
    group_data.sort_values('trade_date', inplace=True)
    group_data['next_day_return'] = (group_data['close'].shift(-1) - group_data['close']) / group_data['close']
    group_data['next_day_open'] = group_data['open'].shift(-1)
    group_data['next_day_high'] = group_data['high'].shift(-1)
    group_data = group_data.apply(lambda x: add_return(x),axis=1)
    if add_return_pd is None:
        add_return_pd = group_data
    else:
        add_return_pd = pd.concat([add_return_pd,group_data])
add_return_pd.to_csv('add_return.csv')