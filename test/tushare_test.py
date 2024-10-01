import xcsc_tushare as ts
ts.set_token('4d0cd91bc89c0e6883fe730fb5bebdca577879eedae349e2feb2acc9')
pro = ts.pro_api(env='prd',server='http://116.128.206.39:7172')
df = pro.bond_redem_pr()
print(df)