#encoding:gbk
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
    return day_data



def init(ContextInfo):
    ContextInfo.my_positions=[]
    ContextInfo.stop_win_ratio = 0.06
    ContextInfo.change_percentile = 100
    ContextInfo.num_stocks = 5
    ContextInfo.per_amount = 10000
    ContextInfo.accId='87000986'
    # 加载模型
    with open('D:\quant\data\lude\model.pkl', 'rb') as file:
        ContextInfo.loaded_model = pickle.load(file)
    ContextInfo.use_columns = ['bias_5', 'dblow', 'remain_size', 'remain_cap',
                    'total_mv', 'left_years', 'pct_chg',
                    'volatility_stk', 'conv_prem',
                    'ytm', 'bond_prem', 'option_value', 'vol',
                    'amount', 'pct_chg_stk', 'turnover',
                    'pct_chg_5', 'pct_chg_5_stk', 'open_pct_chg',
                    'high_pct_chg', 'low_pct_chg']
    ContextInfo.run_time("pre_order_for_stop_win","1nDay","2019-10-14 13:20:00","SH")

def pre_order_for_stop_win(ContextInfo):
    position_info = get_trade_detail_data(ContextInfo.accId, 'stock', 'position')
    for i in position_info:
        stock = i.m_strInstrumentID
        if i.m_strExchangeName == '上证所':
            stock = stock + ".SH"
        if i.m_strExchangeName == '深交所':
            stock = stock + ".SZ"
        volume = i.m_nVolume
        df = ContextInfo.get_market_data_ex(['close'], stock_code=[stock], period='1d',count=2)
        print(df)
        df = df[stock].iloc[0]['close']
        stop_win_price = df * (1 + ContextInfo.stop_win_ratio)
        if volume>0:
            print(stock + "挂止盈单" + str(df))
            passorder(24, 1101, ContextInfo.accId, stock, 6, stop_win_price, volume, ContextInfo)


def handlebar(ContextInfo):
    index = ContextInfo.barpos
    this_date = datetime.fromtimestamp(ContextInfo.get_bar_timetag(index)/1000)
    this_date_str = datetime.strftime(this_date, "%Y-%m-%d %H:%M:%S")
    ContextInfo.current_date_obj = datetime.strftime(this_date, "%Y-%m-%d")
    print(this_date_str)
    position_info = get_trade_detail_data(ContextInfo.accId, 'stock', 'position')
    ContextInfo.my_positions = []
    for i in position_info:
        stock = i.m_strInstrumentID
        if i.m_strExchangeName == '上证所':
            stock = stock + ".SH"
        if i.m_strExchangeName == '深交所':
            stock = stock + ".SZ"
        volume = i.m_nVolume
        if volume>0:
            ContextInfo.my_positions.append(stock)
    if this_date_str[-8:] == "14:55:00":
        print("开始选债")
        cancel_order(ContextInfo)
        selectOrder(ContextInfo)
    pass

def selectOrder(ContextInfo):
    day_data = queryCBInfo(ContextInfo)
    if day_data.empty:
        return []
    day_data['open_pct_chg'] = (day_data['open'] - day_data['pre_close']) / day_data['pre_close']
    day_data['high_pct_chg'] = (day_data['high'] - day_data['pre_close']) / day_data['pre_close']
    day_data['low_pct_chg'] = (day_data['low'] - day_data['pre_close']) / day_data['pre_close']
    day_data = removeCall(day_data)
    use_data = fillNanWithMean(day_data[ContextInfo.use_columns])
    scaler = MinMaxScaler()
    X_test = scaler.fit_transform(use_data.rank())
    y_pred = ContextInfo.loaded_model.predict(X_test)
    num_stocks = ContextInfo.num_stocks
    codes = day_data['code'].values
    limit_y =  np.percentile(y_pred, ContextInfo.change_percentile)
    pred_dict = dict(zip(codes, y_pred))
    position_y =[[key,pred_dict.get(key)] for key in ContextInfo.my_positions]
    position_df = pd.DataFrame(position_y,columns=['code','y'])
    sell_num_limit = len(position_df[position_df['y']<limit_y])
    ContextInfo.my_positions  = list(position_df.sort_values(by=['y'], ascending=True)['code'])
    top_indices = np.argsort(y_pred)[-num_stocks:]
    select_code = day_data.iloc[top_indices]['code'].values
    print(select_code)
    need_remove=[]
    sell_count = 0
    for mycode in ContextInfo.my_positions:
        if sell_count<sell_num_limit and mycode not in select_code:
            # clear
            print(f"卖出 {mycode}")
            order_target_percent(mycode, 0,'COMPETE', ContextInfo, ContextInfo.accId)
            need_remove.append(mycode)
            sell_count = sell_count + 1
    for i in need_remove:
        ContextInfo.my_positions.remove(i)
    need_buy_num = num_stocks - len(ContextInfo.my_positions)
    j = 0
    need_append=[]
    for code in select_code:
        if j<need_buy_num and code not in ContextInfo.my_positions:
            print(f"买入 {code}")
            order_target_value(code, ContextInfo.per_amount, 'COMPETE', ContextInfo,ContextInfo.accId)
            need_append.append(code)
            j = j + 1
    for i in need_append:
        ContextInfo.my_positions.append(i)
    return need_append
    pass

def queryCBInfo(ContextInfo):
    df = None
    retry = 0
    while df is None and retry < 5:
        print("开始查询lude")
        url = "https://lude.cc/api/cb_data_intraday"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data)
        else:
            time.sleep(1)
            retry += 1
            print(f"请求失败，状态码: {response.status_code}，错误信息: {response.text}")
    return df

def cancel_order(ContextInfo):
    orders = get_trade_detail_data(ContextInfo.accId, 'stock', 'ORDER')
    for j in orders:
        order_stock = j.m_strInstrumentID
        if j.m_strExchangeName == '上证所':
            order_stock = order_stock + ".SH"
        if j.m_strExchangeName == '深交所':
            order_stock = order_stock + ".SZ"
        if j.m_dCancelAmount == 0 :
            cancel(j.m_strOrderSysID,ContextInfo.accId, 'STOCK', ContextInfo)

# def queryCBInfo(ContextInfo):
#     aniu_df = query_aniudata(ContextInfo)
#     call_df = cb_call()
#     cb_code_list = aniu_df['bondCode'].values
#     stk_code_list = aniu_df['stockCode'].values
#     cb_dic = ContextInfo.get_market_data_ex(['open','close','high','low','volume'], stock_code=list(cb_code_list), period='1d',count=5)
#     stock_dic = ContextInfo.get_market_data_ex(['close'], stock_code=list(stk_code_list), period='1d',count=5)

#     data_list = []
#     for key,price_data in cb_dic.items():
#         aniu_data = aniu_df[aniu_df['bondCode'] == key]
#         stock_code = aniu_data['stockCode'].values[0]
#         stock_price_data = stock_dic[stock_code]
#         bias_5= aniu_data['bondFiveDayBias']
#         dblow = aniu_data['doubleLow']
#         remain_size = aniu_data['remainSize']
#         remain_cap = aniu_data['remainCap']
#         total_mv = aniu_data['stockTotalValue']
#         left_years = aniu_data['remainYears']
#         pct_chg = aniu_data['chgPct']
#         volatility_stk = aniu_data['oneYearStockVix']
#         conv_prem = aniu_data['bondPrem']
#         ytm = aniu_data['ytmRate']
#         bond_prem = aniu_data['pureBondPrem']
#         option_value = aniu_data['optionVal']
#         vol = price_data.iloc[4]['volume']
#         amount = aniu_data['amount']
#         pct_chg_stk = aniu_data['stockChgPct']
#         turnover = aniu_data['turnoverRate']
#         # 从QMT取
#         pct_chg_5 = aniu_data['chgPct5']
#         pct_chg_5_stk = aniu_data['stockChgPct5']
#         open_pct_chg = aniu_data['openChgPct']
#         high_pct_chg = aniu_data['highChgPct']
#         low_pct_chg = aniu_data['lowChgPct']
#         code = key
#         is_call = ''
#         this_code_call_df = call_df[call_df['ts_code'] == code]
#         if  this_code_call_df is not None and this_code_call_df.empty is False:
#             this_code_call_df = this_code_call_df.sort_values('ann_date', ascending=False)
#             is_call = this_code_call_df['is_call'].values[0]
#         data_list.append([bias_5, dblow, remain_size, remain_cap,
#                 total_mv, left_years, pct_chg,
#                 volatility_stk, conv_prem,
#                 ytm, bond_prem, option_value, 0,
#                 amount, pct_chg_stk, turnover,
#                 pct_chg_5, pct_chg_5_stk, open_pct_chg,
#                 high_pct_chg, low_pct_chg,code,is_call])
#     day_data = pd.DataFrame(data_list,columns=ContextInfo.all_columns)
#     return day_data


# def query_aniudata( ContextInfo):
#     df = None
#     retry = 0
#     while df is None and retry < 5:
#         # 假设这里有有效的令牌，实际使用时需要替换为真实令牌
#         token = "390f9d0a85c44b75acfd5a35e5648b7f"
#         headers = {
#             "Authorization": f"Bearer {token}"
#         }
#         url = "https://lude.cc/api/cb_data_intraday"+token
#         response = requests.get(url, headers=headers)
#         if response.status_code == 200:
#             data = response.json()['data']
#             df = pd.DataFrame(data)
#         else:
#             time.sleep(1)
#             retry += 1
#             print(f"请求失败，状态码: {response.status_code}，错误信息: {response.text}")
#     return df

# def cb_call():
#     df = None
#     retry = 0
#     while df is None and retry < 5:
#         try:
#             xc.set_token('4d0cd91bc89c0e6883fe730fb5bebdca577879eedae349e2feb2acc9')
#             pro = ts.pro_api(env='prd',server='http://116.128.206.39:7172')
#             df = pro.cb_call(fields=['ts_code', 'ann_date', 'call_type', 'is_call'])
#         except BaseException as e:
#             log.exception(e)
#             time.sleep(1)
#             retry += 1
#     return df


























