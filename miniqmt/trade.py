
import os
import pickle
import random
import time
from multiprocessing import Queue, Process
from typing import Iterable
from xtquant.xttrader import XtQuantTraderCallback

import datetime
import akshare
import numpy
import numpy as np
import pandas
import xtquant
from xtquant import xtconstant
from xtquant.xttrader import XtQuantTrader, XtQuantTraderCallback
from xtquant.xttype import StockAccount
from pandas import Series

from GUI import GUI

'''
定义常数-----------------------------------------------------
'''
BUY_ORDER_TBD = 11
#待报订单，程序发出指令后但回报函数未回报状态
BUY_ORDER_PD = 12
#已报订单，程序发出指令后回报函数已经回报
BUY_ORDER_CC_TBD = 21
#待撤订单，程序发出指令后回报函数未回报状态
SELL_ORDER_TBD = 31
#待报订单，程序发出指令后但回报函数未回报状态
SELL_ORDER_PD = 32
#已报订单，程序发出指令后回报函数已经回报
SELL_ORDER_CC_TBD = 41
#待撤订单，程序发出指令后回报函数未回报状态
END = 51
#已经卖出，结束
POS = 61
#正在持仓，无其他指令

'''
定义常数-----------------------------------------------------
'''




class Trade(XtQuantTraderCallback):
    def __init__(self):
        #dict结构:code:{order_status:(),buy_order_id:(),sell_order_id:(),is_responded:True/False}
        self.sleep_time = 60
        self.order_amount = 10000
        self.strategy_name = "lstm"
    def initial_trade(self):
        self.path = r'D:\quant\国金证券QMT交易端\userdata_mini'
        self.session_id = random.randint(100000, 999999)
        self.xt_trader = XtQuantTrader(self.path, self.session_id)

        # self.xt_trader.set_relaxed_response_order_enabled(True)
        self.acc = StockAccount('87000986')

        callback = self
        self.xt_trader.register_callback(callback)
        # 启动交易线程
        self.xt_trader.start()
        # 建立交易连接，返回0表示连接成功
        connect_result = self.xt_trader.connect()
        if connect_result != 0:
            import sys
            sys.exit('链接失败，程序即将退出 %d' % connect_result)
        subscribe_result = self.xt_trader.subscribe(self.acc)
        if subscribe_result != 0:
            print('账号订阅失败 %d' % subscribe_result)
    '''
    回调类函数-------------------------------------------------------------------------------------------------------
    '''

    def on_disconnected(self):
        """
        连接断开
        :return:
        """
        print("connection lost")

    def on_stock_order(self, order):
        """
        委托回报推送
        :param order: XtOrder对象
        :return:
        """
        print("我是委托回报推送")
        print(order.stock_code, order.order_status, order.order_sysid)

    def on_stock_asset(self, asset):
        """
        资金变动推送  注意，该回调函数目前不生效
        :param asset: XtAsset对象
        :return:
        """
        print("on asset callback")
        print(asset.account_id, asset.cash, asset.total_asset)

    def on_stock_trade(self, trade):
        """
        成交变动推送
        :param trade: XtTrade对象
        :return:
        """
        print("已经成交！！！")
        print(trade.account_id, trade.stock_code, trade.order_id)

    def on_stock_position(self, position):
        """
        持仓变动推送  注意，该回调函数目前不生效
        :param position: XtPosition对象
        :return:
        """
        print("on position callback")
        print(position.stock_code, position.volume)

    def on_order_error(self, order_error):
        """
        委托失败推送
        :param order_error:XtOrderError 对象
        :return:
        """
        print("on order_error callback")
        print(order_error.order_id, order_error.error_id, order_error.error_msg)

    def on_cancel_error(self, cancel_error):
        """
        撤单失败推送
        :param cancel_error: XtCancelError 对象
        :return:
        """
        print("on cancel_error callback")
        print(cancel_error.order_id, cancel_error.error_id, cancel_error.error_msg)

    def on_order_stock_async_response(self, response):
        """
        异步下单回报推送
        :param response: XtOrderResponse 对象
        :return:
        """
        print("已经下单！！！！")

        print(response.account_id)

        print(response.account_id, response.order_id, response.seq, response.order_remark)

    def on_account_status(self, status):
        """
        :param response: XtAccountStatus 对象
        :return:
        """
        print("on_account_status")
        print(status.account_id, status.account_type, status.status)

    def on_cancel_order_stock_async_response(self, response):
        """
        :param response: XtCancelOrderResponse 对象
        :return:
        """
        print('异步撤单回报')

    def stop_in_rest_time(self):
        today = datetime.datetime.today()
        end_time = datetime.datetime(today.year, today.month, today.day, 11, 30, 0)
        start_time = datetime.datetime(today.year, today.month, today.day, 13, 00, 0)
        if (today > end_time and today < start_time):
            time.sleep((start_time - today).total_seconds() + 2)
        return self
    def change_parm(self,parm_name,value):
        if(parm_name=='每单持仓'):
            self.order_amount = value
        else:
            print('变量不存在')
        return




    def trade(self):
        self.initial_trade()
        '''
        外部初始化区分割线---------------------------------------------
        '''
        '''
        外部初始化区分割线---------------------------------------------
        '''
        while True:
            self.stop_in_rest_time()
            '''
            调用区分割线-------------------------------------------
            '''

            '''
            调用区分割线-------------------------------------------
            '''
            # self.send_detail_value(detail_queue)
            time.sleep(self.sleep_time)




if __name__ == '__main__':
    p_trade = Process(target=Trade().trade)
    p_trade.start()
    p_trade.join()
