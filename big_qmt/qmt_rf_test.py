# encoding:gbk
# encoding:gbk
import pandas as pd
import numpy as np
import talib
import pickle
from datetime import datetime
import time
import requests
from sklearn.preprocessing import MinMaxScaler


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
    day_data = day_data[day_data['limit'] != 1]
    return day_data


def init(ContextInfo):
    ContextInfo.my_positions = []
    ContextInfo.stop_win_ratio = 0.06
    ContextInfo.accId = '87000986'
    ContextInfo.today_newadd = []
    ContextInfo.cb_data = pd.read_csv('D:/quant/data/lude/test_data_for_backtest.csv')
    ContextInfo.current_date_obj = None
    ContextInfo.turn_rate_limit = 0.9
    ContextInfo.num_stocks = 10
    ContextInfo.change_percentile = 100
    # 加载模型
    with open('D:\quant\data\lude\model-for-test.pkl', 'rb') as file:
        ContextInfo.loaded_model = pickle.load(file)


def handlebar(ContextInfo):
    if ContextInfo.is_last_bar():
        index = ContextInfo.barpos
        this_date = datetime.fromtimestamp(ContextInfo.get_bar_timetag(index) / 1000)
        this_date_str = datetime.strftime(this_date, "%Y-%m-%d %H:%M:%S")
        bar_date = datetime.strftime(this_date, "%Y%m%d%H%M%S")
        ContextInfo.current_date_obj = datetime.strftime(this_date, "%Y-%m-%d")
        if this_date_str[-8:] == "09:30:00":
            ContextInfo.today_newadd = []
        if this_date_str[-8:] == "14:55:00":
            ContextInfo.trade_date = this_date_str[:10]
            ContextInfo.today_newadd = select_stock(ContextInfo)
        for stock in ContextInfo.my_positions:
            if stock in ContextInfo.today_newadd:
                continue
            df = ContextInfo.get_market_data_ex(['close'], end_time=bar_date, stock_code=[stock], period='1d', count=2)
            if df[stock].empty:
                continue
            df = df[stock].iloc[0]['close']
            stop_win_price = df * (1 + ContextInfo.stop_win_ratio)
            minu_data = ContextInfo.get_market_data_ex(['close'], end_time=bar_date, stock_code=[stock], period='1m',
                                                       count=1)
            if minu_data[stock].empty:
                continue
            minu_data = minu_data[stock].iloc[0]['close']
            if minu_data >= stop_win_price:
                print(stock + "触发止赢:当前价格" + str(minu_data) + ";昨日价格:" + str(df))
                order_target_percent(stock, 0, ContextInfo, ContextInfo.accId)
                ContextInfo.my_positions.remove(stock)


def select_stock(ContextInfo):
    new_columns = ['bias_5', 'dblow', 'remain_size', 'remain_cap',
                   'total_mv', 'left_years', 'pct_chg',
                   'volatility_stk', 'conv_prem',
                   'ytm', 'bond_prem', 'option_value', 'vol',
                   'amount', 'pct_chg_stk', 'turnover',
                   'pct_chg_5', 'pct_chg_5_stk', 'open_pct_chg',
                   'high_pct_chg', 'low_pct_chg']
    print(ContextInfo.current_date_obj)

    day_data = ContextInfo.cb_data[ContextInfo.cb_data['trade_date'] == ContextInfo.current_date_obj]
    if day_data.empty:
        return []
    day_data = removeCall(day_data)
    use_data = fillNanWithMean(day_data[new_columns])
    scaler = MinMaxScaler()
    X_test = scaler.fit_transform(use_data.rank())
    y_pred = ContextInfo.loaded_model.predict(X_test)
    # print(y_pred)
    num_stocks = ContextInfo.num_stocks
    codes = day_data['code'].values
    limit_y = np.percentile(y_pred, ContextInfo.change_percentile)
    pred_dict = dict(zip(codes, y_pred))
    position_y = [[key, pred_dict.get(key)] for key in ContextInfo.my_positions]
    position_df = pd.DataFrame(position_y, columns=['code', 'y'])
    sell_num_limit = len(position_df[position_df['y'] < limit_y])
    ContextInfo.my_positions = list(position_df.sort_values(by=['y'], ascending=True)['code'])
    top_indices = np.argsort(y_pred)[-num_stocks:]
    select_code = day_data.iloc[top_indices]['code'].values
    need_remove = []
    sell_count = 0
    for mycode in ContextInfo.my_positions:
        if sell_count < sell_num_limit and mycode not in select_code:
            # clear
            print(f"卖出 {mycode}")
            order_target_percent(mycode, 0, ContextInfo, '87000986')
            need_remove.append(mycode)
            sell_count = sell_count + 1
    for i in need_remove:
        ContextInfo.my_positions.remove(i)
    need_buy_num = num_stocks - len(ContextInfo.my_positions)
    j = 0
    need_append = []
    for code in select_code:
        if j < need_buy_num and code not in ContextInfo.my_positions:
            print(f"买入 {code}")
            order_target_value(code, 20000, 'COMPETE', ContextInfo, '87000986')
            need_append.append(code)
            j = j + 1
    for i in need_append:
        ContextInfo.my_positions.append(i)
    return need_append
    pass