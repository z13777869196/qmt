import pandas
from keras.layers import Bidirectional, Attention
from keras.optimizers.optimizer_v1 import Adam
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping
from sklearn.preprocessing import StandardScaler,MinMaxScaler
from datetime import datetime

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pickle
from sklearn.metrics import accuracy_score, mean_squared_error
from sklearn.metrics import r2_score
from scipy.stats import spearmanr
from tensorflow.keras.models import load_model
import tensorflow as tf
import quantstats as qs
from tensorflow.keras.callbacks import EarlyStopping
from keras_self_attention import SeqSelfAttention  # 导入注意力层‌:ml-citation{ref="1,2" data="citationList"}


from backtest.backtrader.pre_handle_data.utils import generate_rank_data, removeCall, fillNanWithMean

period = 1
slip_ratio = 0.002
num_stocks =40
group_num = 30
change_percentile = 100
need_train = True
target_key = 'next_day_return_stop_win6'
cal_return_target_key = 'next_day_return_stop_win6'
scaler = MinMaxScaler()
time_period = 30
# 构造时间序列样本
def create_dataset(train_data,factors,target,time_steps=time_period,need_valid_data=False):
    X, y = [], []
    x_valid,y_valid = [],[]
    daily_x,daily_y = {}, {}
    for code,code_data in train_data.groupby('code'):
        for i in range(len(code_data)-time_steps+1):
            date = code_data.iloc[i+time_steps-1].name[1]
            if need_valid_data is False or date <= '2024-05-01':
                X.append(code_data[i:i+time_steps][factors])
                y.append(code_data.iloc[i+time_steps-1][target])     # 目标为第30天的Y值
            else:
                x_valid.append(code_data[i:i+time_steps][factors])
                y_valid.append(code_data.iloc[i+time_steps-1][target])

            if date in daily_x:
                daily_x[date].append(code_data[i:i+time_steps][factors])
                daily_y[date].append(code_data.iloc[i+time_steps-1][target])
            else:
                daily_x[date] = [code_data[i:i+time_steps][factors]]
                daily_y[date] = [code_data.iloc[i+time_steps-1][target]]
    return np.array(X), np.array(y),np.array(x_valid), np.array(y_valid),daily_x,daily_y
# 定义早停回调
early_stopping = EarlyStopping(
    monitor='val_loss',      # 监控验证集损失
    patience=10,             # 允许连续10轮无改善
    restore_best_weights=True,  # 恢复最佳权重
    verbose=1                # 打印日志
)

factors =  ['bias_5', 'dblow', 'remain_size','remain_cap',
                  'total_mv', 'left_years', 'pct_chg',
                  'volatility_stk', 'conv_prem',
                  'ytm', 'bond_prem', 'option_value', 'vol',
                  'amount', 'pct_chg_stk', 'turnover',
                  'pct_chg_5', 'pct_chg_5_stk', 'open_pct_chg',
                  'high_pct_chg', 'low_pct_chg','open','high','low','close']
if need_train:
    train_data = pd.read_csv("data/train_data.csv",low_memory=False)
    train_data.set_index(keys=['code','trade_date'], inplace=True)
    train_data,train_y = generate_rank_data(train_data,factors,target_key)
    train_data = train_data.merge(train_y,left_index=True,right_index=True)
    # train_data = train_data[train_data['trade_date']<'2023-10-01']
    x_train,y_train,x_valid,y_valid,daily_x_train,daily_y_train = create_dataset(train_data,factors,target_key,time_period,True)
    # valid_data = train_data[train_data['trade_date']>='2023-10-01']
    # x_valid,y_valid,daily_x_v,daily_y_v = create_dataset(valid_data,factors,cal_return_target_key)

    print("X_train 形状:", x_train.shape)  # 应输出 (n_samples, timesteps, features)

    factor_nums= len(factors)


    # 定义模型
    model = Sequential()
    model.add(Bidirectional(LSTM(128,return_sequences=True, input_shape=(time_period, factor_nums))))
    model.add(SeqSelfAttention(attention_activation='sigmoid'))  # 启用可学习缩放因子
    model.add(Dropout(0.3))
    model.add(LSTM(64))
    model.add(Dense(1))
    model.compile('adam', loss='huber')

    # 训练
    model.fit(x_train, y_train, epochs=100, batch_size=128,  validation_data=(x_valid, y_valid),
    shuffle=False)
    model.save('data/lstm_model.h5')

loaded_model = load_model('data/lstm_model.h5',
                          custom_objects={'SeqSelfAttention': SeqSelfAttention}
)

# 4. 模型预测
all_test = pd.read_csv("data/test_data.csv",low_memory=False)
all_test.set_index(keys=['code', 'trade_date'], inplace=True)
test_data,test_y = generate_rank_data(all_test,factors,cal_return_target_key)

test_data = test_data.merge(test_y, left_index=True, right_index=True)

x_test,y_test,x_valid,y_valid,daily_x_test,daily_y_test = create_dataset(test_data,factors,cal_return_target_key)
print("x_test 形状:", x_test.shape)  # 应输出 (n_samples, timesteps, features)
y_pred = loaded_model.predict(x_test)
# 评估模型
mse = mean_squared_error(y_test, y_pred)
print(f"均方误差 (MSE): {mse}")
r2 = r2_score(y_test, y_pred)
print(f"R2：{r2}")
ic, p_value = spearmanr(y_pred, y_test)
print(f"ic：{ic},pValue:{format(p_value, '.10e')}")
same_sign_count = 0
for num1, num2 in zip(y_test, y_pred):
    # 判断两个元素是否同正或同负
    if (num1 > 0 and num2 > 0) or (num1 < 0 and num2 < 0):
        same_sign_count += 1
    # 计算同正同负的比例
ratio = same_sign_count / len(y_test)
print(f"同正同负比例：{ratio}")

# top_percentage = 0.2
# num_stocks = int(len(y_pred) * top_percentage)
# top_indices = np.argsort(y_pred)[-num_stocks:]

y_test = pd.Series(y_test)

# 可视化预测结果与实际结果
plt.scatter(y_test, y_pred)
plt.xlabel('actual')
plt.ylabel('predict')
plt.title('actual vs predict')
plt.show()

count = 0
ics = []
returns_dic = {}
all_pred_return = 0
all_return = 0
turnRate = []
position = []
group_return = {}
buy_count = 0
sell_count = 0
all_mse = 0
for date, day_data in daily_x_test.items():
    if count % period == 0:

        # X_test = use_data.rank()

        # X_test = scaler.fit_transform(use_data)
        y_test= np.array(daily_y_test[date])

        # print(day_data)
        y_pred_two = np.array(loaded_model.predict(np.array(day_data)))
        y_pred = [element for sublist in y_pred_two for element in sublist]
        # print(y_pred)
        # print(y_test)
        mse = mean_squared_error(y_test, y_pred)
        all_mse = all_mse + mse
        ic, p_value = spearmanr(y_pred, y_test)
        ics.append(ic)

        sell_num_limit = num_stocks

        top_indices = np.argsort(y_pred)[-num_stocks:]
        # print(top_indices)
        today_code =[day_data[i].reset_index()['code'].values[0] for i in top_indices]
        act_ret = [y_test[i] for i in top_indices]
        # print(today_code)
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
        # print(act_ret)
        portfolio_return = np.mean(act_ret)-turn_rate*slip_ratio


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
            selected_returns = [y_test[i] for i in indices]
            group_return[i] = group_return[i] + np.mean(selected_returns)

        turnRate.append(turn_rate)
        date = datetime.strptime(date, '%Y-%m-%d')
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
index = pandas.read_csv("data/index.csv")
benchmark = index[['trade_date','index_jsl']]
benchmark = benchmark[benchmark['trade_date']>='2024-01-01']
benchmark['trade_date'] = pd.to_datetime(benchmark['trade_date'])
benchmark.set_index('trade_date', inplace=True)
# print(returns_df)
qs.reports.html(returns_df,benchmark=benchmark, output='lstm-stats.html', title='Stock Sentiment')
