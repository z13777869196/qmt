import xcsc_tushare as ts
ts.set_token('4d0cd91bc89c0e6883fe730fb5bebdca577879eedae349e2feb2acc9')
pro = ts.pro_api(env='prd',server='http://116.128.206.39:7172')
# df = pro.cb_call(ts_code='110052.SH',fields=['ts_code', 'ann_date', 'call_type', 'is_call'])
# print( df)
#
# df = pro.stk_mins(ts_code='123089.SH',start_time='2025-03-12 09:30:00',end_time='2025-03-12 15:00:00',freq='5min')
# print( df)

df = pro.index_daily(ts_code= '000852.SH',trade_date="20210526",fields="ts_code,trade_date,pre_close,close,change,pct_chg")
print(df)

df = pro.index_daily(ts_code= '399303.SZ',trade_date="20210526",fields="ts_code,trade_date,pre_close,close,change,pct_chg")
print(df)

df = pro.daily_basic_ts(trade_date="20250526")
print(df)