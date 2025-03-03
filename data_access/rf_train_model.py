import pandas
from sklearn.ensemble import RandomForestRegressor
import pandas as pd
import matplotlib.pyplot as plt
import pickle
import numpy as np
from scipy.stats import spearmanr
import quantstats as qs
from sklearn.metrics import mean_squared_error

from sklearn.preprocessing import StandardScaler, MinMaxScaler

from backtest.backtrader.pre_handle_data.utils import analysis_result, fillNanWithMean, removeCall

need_train = False
train_data = pd.read_csv("data/train_data.csv",low_memory=False)
all_test = pd.read_csv("data/test_data.csv",low_memory=False)

# all_test = all_test[all_test['trade_date']>'2022-08-01']
scaler = MinMaxScaler()

target_key = 'next_day_return_stop_win6'
cal_return_target_key = 'next_day_return_stop_win6'
period = 1
slip_ratio = 0.002
num_stocks =40
group_num = 30
change_percentile = 100
# target_key='next_day_return'

new_columns =  ['bias_5', 'dblow', 'remain_size','remain_cap',
                  'total_mv', 'left_years', 'pct_chg',
                  'volatility_stk', 'conv_prem',
                  'ytm', 'bond_prem', 'option_value', 'vol',
                  'amount', 'pct_chg_stk', 'turnover',
                  'pct_chg_5', 'pct_chg_5_stk', 'open_pct_chg',
                  'high_pct_chg', 'low_pct_chg']

# columns_to_exclude = ['open_stk','high_stk','low_stk','close_stk','pre_close_stk','popularity_ranking','adj_factor','limit', 'maturity', 'maturity_put_price', 'issue_size', 'conv_price','Unnamed: 0','rating','yy_rating','orgform','area','industry_1','industry_2','industry_3','list_date','conv_start_date','conv_end_date','is_call','datetime','code','trade_date','name','code_stk','name_stk','next_day_return','next_day_open','next_day_high','next_day_return_stop_win3','next_5day_return','next_8day_return','next_day_return_stop_win6','next_5day_return_stop_win3','next_3day_return_stop_win3']
# new_columns = [col for col in train_data.columns if col not in columns_to_exclude]
# rf = RandomForestRegressor(n_estimators=100, max_depth=40,max_features='sqrt',min_samples_leaf=20, random_state=42, n_jobs=-1)
rf = RandomForestRegressor(n_estimators=100, max_depth=40,max_features=1.0,min_samples_leaf=20, random_state=42, n_jobs=-1)

x_train = None
y_train = None
for date, day_data in train_data.groupby('datetime'):
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
# x_train = use_data
# y_train = train_data[target_key]
# print(x_train)
if need_train:
    rf.fit(x_train, y_train)
    # 保存模型
    with open('model/rf.pkl', 'wb') as file:
        pickle.dump(rf, file)

# 加载模型
with open('model/rf.pkl', 'rb') as file:
    loaded_model = pickle.load(file)

# 获取特征重要性
feature_importances = pd.Series(loaded_model.feature_importances_, index=new_columns)
# feature_importances = feature_importances[feature_importances > 0.02]
feature_importances.sort_values(ascending=False, inplace=True)
feature_importances.plot(kind='bar')
print(feature_importances)

# 设置标题和坐标轴标签
plt.title('Factor Importance')
plt.xlabel('Factor')
plt.ylabel('Values')
plt.show()

# 加载测试数据
# all_test_scaler = use_test_data.rank()
# all_test_scaler = scaler.fit_transform(use_test_data)
# # 整体数据预测
# all_y_test = all_test[target_key]
# all_y_pred = loaded_model.predict(all_test_scaler)
# analysis_result(all_y_test, all_y_pred)
# 每天数据预测
ics = []
returns_dic = {}
all_pred_return = 0
all_return = 0
turnRate = []
position = []
all_test['datetime'] = pd.to_datetime(all_test.trade_date)

count = 0

group_return = {}
buy_count = 0
sell_count = 0
all_mse = 0
for date, day_data in all_test.groupby('datetime'):
    if count % period == 0:
        day_data = removeCall(day_data)
        use_data = fillNanWithMean(day_data[new_columns])
        X_test = scaler.fit_transform(use_data.rank())
        # X_test = use_data.rank()

        # X_test = scaler.fit_transform(use_data)
        y_test = day_data[cal_return_target_key]
        y_pred = loaded_model.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        all_mse = all_mse + mse
        ic, p_value = spearmanr(y_pred, y_test)
        ics.append(ic)

        code = day_data['code'].values
        limit_y =  np.percentile(y_pred, change_percentile)
        pred_dict = dict(zip(code, y_pred))
        position_y =[[key,pred_dict.get(key)] for key in position]
        position_df = pd.DataFrame(position_y,columns=['code','y'])
        position_df = position_df.sort_values(by=['y'], ascending=True)
        sell_num_limit = len(position_df[position_df['y']<limit_y])
        sell_num_limit = num_stocks
        print(sell_num_limit)
        position  = list(position_df['code'])

        top_indices = np.argsort(y_pred)[-num_stocks:]
        today_code = day_data.iloc[top_indices]['code'].values
        need_remove = []
        j = 0
        for code in position:
            if j < sell_num_limit and code not in today_code:
                need_remove.append(code)
                j = j + 1
        for code in need_remove:
            position.remove(code)
        sell_count = sell_count+j
        need_num = num_stocks - len(position)
        need_add = []
        i = 0
        for code in today_code:
            if i < need_num and code not in position:
                i = i + 1
                need_add.append(code)
        for code in need_add:
            position.append(code)
        buy_count = buy_count+i
        turn_rate = len(need_add) / num_stocks
        # print(position)
        act_ret = day_data[day_data['code'].isin(position)][cal_return_target_key]
        # print(act_ret)
        portfolio_return = act_ret.mean()-turn_rate*slip_ratio


        # 分组
        group_count = int(len(y_test) / group_num)
        for i in range(group_num):
            if i not in group_return:
                group_return[i] = 0
            start_index = group_count * i
            end_index = group_count * (i + 1)
            if i == 0:
                indices = np.argsort(y_pred)[-end_index:]
            else:
                indices = np.argsort(y_pred)[-end_index:-start_index]
            selected_returns = y_test.iloc[indices]
            group_return[i] = group_return[i] + selected_returns.mean()

        turnRate.append(turn_rate)
        returns_dic[date] = portfolio_return
        print(f"date:{date} 实际收益率: {portfolio_return}")
        all_return = all_return + portfolio_return
    count = count + 1
print(f"投资组合收益率: {all_return}")
ics = pd.Series(ics)
print(f"日均IC：{ics.mean()};日均IC标准差:{ics.std()}")
print(f"IR: {ics.mean() / ics.std()}")
turnRate = np.array(turnRate)
print(f"换手率：{turnRate.sum() / count}")
print(f"MSE：{all_mse / count}")
print(f"买数量：{buy_count};卖数量：{sell_count}")
print(f"分组平均收益率:{np.mean(list(group_return.values()))},分组收益率{group_return}")
# 绘制直方图
plt.bar(group_return.keys(), group_return.values())

# 设置图表标题和坐标轴标签
plt.title('Group Return')
plt.xlabel('Group')
plt.ylabel('Return')

# 显示图表
plt.show()
returns_df = pd.Series(returns_dic)
print(returns_df)
index = pandas.read_csv("data/index.csv")
benchmark = index[['trade_date','index_jsl']]
benchmark = benchmark[benchmark['trade_date']>='2024-01-01']
benchmark['trade_date'] = pd.to_datetime(benchmark['trade_date'])
benchmark.set_index('trade_date', inplace=True)
qs.reports.html(returns_df, benchmark=benchmark ,output='stats.html', title='Stock Sentiment')
