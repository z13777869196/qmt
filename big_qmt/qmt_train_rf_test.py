#encoding:gbk

from sklearn.ensemble import RandomForestRegressor
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import accuracy_score,mean_squared_error
from sklearn.model_selection import train_test_split
import numpy as np
import pickle
from sklearn.preprocessing import  MinMaxScaler

train_data_pd = pd.read_csv('D:/quant/data/lude/train_data_for_backtest.csv',low_memory=False)

def fillNanWithMean(use_data):
    column_means = use_data.mean()
    # 填充NaN值为每列的均值
    return use_data.fillna(column_means)

def removeCall(day_data):
    day_data = day_data[day_data['is_call'] != '已满足强赎条件']
    day_data = day_data[day_data['is_call'] != '公告提示强赎']
    day_data = day_data[day_data['is_call'] != '公告实施强赎']
    day_data = day_data[day_data['is_call'] != '公告到期赎回']
    day_data = day_data[day_data['is_call'] != '已公告强赎']
    day_data = day_data[day_data['limit']!=1]
    return day_data

target_key = 'next_day_return_stop_win6'
scaler = MinMaxScaler()
columns_to_use = ['bias_5', 'dblow', 'remain_size', 'remain_cap',
                  'total_mv', 'left_years', 'pct_chg',
                  'volatility_stk', 'conv_prem',
                  'ytm', 'bond_prem', 'option_value', 'vol',
                  'amount', 'pct_chg_stk', 'turnover',
                  'pct_chg_5', 'pct_chg_5_stk', 'open_pct_chg',
                  'high_pct_chg', 'low_pct_chg']

new_columns = columns_to_use
x_train = None
y_train = None
for date,day_data in train_data_pd.groupby('datetime'):
    day_data = removeCall(day_data)
    use_data = fillNanWithMean(day_data[new_columns])
    if x_train is None:
        # x_train = scaler.fit_transform(use_data)
        x_train = use_data.rank()
        x_train = scaler.fit_transform(x_train)
        y_train = day_data[target_key]
    else:
        # x_train = np.vstack((x_train, scaler.fit_transform(use_data)))
        # x_train =  pd.concat([x_train, use_data.rank()])
        x_train = np.vstack([x_train, scaler.fit_transform(use_data.rank())])

        y_train = pd.concat([y_train, day_data[target_key]])

rf = RandomForestRegressor(n_estimators=100, max_depth=40,max_features=1.0,min_samples_leaf=20, random_state=42, n_jobs=-1)

rf.fit(x_train, y_train)

with open('D:/quant/data/lude/model-for-test.pkl', 'wb') as file:
    pickle.dump(rf, file)