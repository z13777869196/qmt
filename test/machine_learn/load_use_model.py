from fontTools.misc.cython import returns
from sklearn.ensemble import RandomForestRegressor
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import accuracy_score,mean_squared_error,mean_absolute_percentage_error
from sklearn.model_selection import train_test_split
import numpy as np
import pickle
from datetime import datetime
import quantstats as qs

add_return_pd = pd.read_csv('add_return.csv',low_memory=False)
add_return_pd['datetime'] = pd.to_datetime(add_return_pd.trade_date)

train_data= add_return_pd[add_return_pd['datetime']<=datetime(2025, 12, 31)]
train_data = train_data[train_data['datetime']>=datetime(2024, 1, 1)]
train_data = train_data.dropna(subset=['next_day_return'])
# 加载模型
with open('model.pkl', 'rb') as file:
    loaded_model = pickle.load(file)
all_return=0
all_pred_return=0
returns_dic={}
for date,day_data in train_data.groupby('datetime'):
    columns_to_exclude = ['adj_factor','popularity_ranking', 'limit', 'maturity', 'maturity_put_price', 'issue_size', 'high_stk', 'close_stk', 'conv_price', 'low_stk', 'open_stk','Unnamed: 0','rating','yy_rating','orgform','area','industry_1','industry_2','industry_3','list_date','conv_start_date','conv_end_date','is_call','datetime','code','trade_date','name','code_stk','name_stk','next_day_return','next_day_open','next_day_high','next_day_return_stop_win3','next_day_return_stop_win6']
    columns_to_use = ['bias_5', 'pct_chg', 'pct_chg_5', 'open', 'high', 'low', 'close', 'vol',
                      'pct_chg_5_stk', 'vol_5', 'vol_stk',
                      'debt_to_assets']

    new_columns = [col for col in train_data.columns if col not in columns_to_exclude]
    new_columns = columns_to_use
    use_data =day_data[new_columns]
    column_means = use_data.mean()
    # 填充NaN值为每列的均值
    use_data = use_data.fillna(column_means)
    X_test= use_data
    y_test = day_data['next_day_return_stop_win3']
    # 4. 模型预测
    y_pred = loaded_model.predict(X_test)
    top_percentage = 0.05
    num_stocks = int(len(y_pred) * top_percentage)
    num_stocks = 10
    top_indices = np.argsort(y_pred)[-num_stocks:]
    # 计算选中股票的实际收益率
    selected_returns = y_test.iloc[top_indices]
    selected_pred_returns = y_pred[top_indices]
    portfolio_return = selected_returns.mean()
    pred_return = selected_pred_returns.mean()
    all_pred_return=all_pred_return+ pred_return
    returns_dic[date]=portfolio_return
    print(f"date:{date} 投资组合预测收益率：{pred_return} 实际收益率: {portfolio_return}")
    all_return = all_return+portfolio_return
    # select_data =  train_data.iloc[top_indices]
    # print(select_data)
print(f"投资组合收益率: {all_return}")
print(f"投资组合预测收益率: {all_pred_return}")
returns_df = pd.Series(returns_dic)
qs.reports.html(returns_df, output='stats.html', title='Stock Sentiment')
