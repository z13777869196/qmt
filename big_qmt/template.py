# encoding:gbk
from datetime import datetime

class a(): pass

A = a()
A.has_select_order = False

def init(ContextInfo):
    ContextInfo.stop_win_ratio = 0.06
    ContextInfo.accId = ''
    ContextInfo.need_cancel_status = [48, 49, 50, 55]
    ContextInfo.select_order_time = "14:57:00"
    ContextInfo.run_time("pre_order_for_stop_win", "1nDay", "2025-02-18 09:21:00", "SH")




def pre_order_for_stop_win(ContextInfo):
    A.has_select_order = False
    cancel_order(ContextInfo)
    position_info = get_trade_detail_data(ContextInfo.accId, 'stock', 'position')
    for i in position_info:
        stock = i.m_strInstrumentID
        if i.m_strExchangeName == '上证所':
            stock = stock + ".SH"
        if i.m_strExchangeName == '深交所':
            stock = stock + ".SZ"
        volume = i.m_nVolume
        df = ContextInfo.get_market_data_ex(['close'], stock_code=[stock], period='1d', count=2)
        print(df)
        if df != None and df[stock].empty is False:
            df = df[stock].iloc[0]['close']
            stop_win_price = df * (1 + ContextInfo.stop_win_ratio)
            if volume > 0:
                print(stock + "挂止盈单" + str(stop_win_price))
                passorder(24, 1101, ContextInfo.accId, stock, 11, stop_win_price, volume, 2, ContextInfo)


def handlebar(ContextInfo):
    if ContextInfo.is_last_bar():
        index = ContextInfo.barpos
        this_date = datetime.fromtimestamp(ContextInfo.get_bar_timetag(index) / 1000)
        this_date_str = datetime.strftime(this_date, "%Y-%m-%d %H:%M:%S")
        ContextInfo.current_date_obj = datetime.strftime(this_date, "%Y-%m-%d")
        print(this_date_str)
        if A.has_select_order == False and this_date_str[-8:] == ContextInfo.select_order_time:
            print("开始选债")
            cancel_order(ContextInfo)
            selectOrder(ContextInfo)
            A.has_select_order = True


def selectOrder(ContextInfo):
    # todo 选债
    # 构建买卖的篮子
    table = []
    basket={'name':'debt_basket','stocks':table}
    set_basket(basket)
    # 下单
    algoParam={
    'm_dLimitOverRate': 0.25,      # 量比 25%
    'm_dMinAmountPerOrder':10000,      # 委托最小金额
    'm_dMaxAmountPerOrder':30000,  # 委托最大金额
    'm_nStopTradeForOwnHiLow': 0,  # 涨跌停控制
    'm_dMulitAccountRate':0.30,    # 多账号总量比
    'm_strCmdRemark':  '篮子下单'  # 投资备注
    }
    smart_algo_passorder(
        35,
        2101,
        ContextInfo.accId,
        'debt_basket',
        12,              #市价
        0,             #数量
        1,              #按篮子下单
        '',      #策略名
        2,               # quickTrade
        '篮子下单',
        'TWAP',
        "10:25:00",      # 开始时间
        "15:00:00",      # 结束时间
        algoParam,       # 算法参数
        ContextInfo
        )

def cancel_order(ContextInfo):
    orders = get_trade_detail_data(ContextInfo.accId, 'stock', 'ORDER')
    for j in orders:
        print(j.m_nOrderStatus)
        if j.m_nOrderStatus in ContextInfo.need_cancel_status:
            cancel(j.m_strOrderSysID, ContextInfo.accId, 'STOCK', ContextInfo)
