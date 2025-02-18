from sklearn.ensemble import RandomForestRegressor
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import accuracy_score,mean_squared_error
from sklearn.model_selection import train_test_split
import numpy as np
import pickle


train_data_pd = pd.read_csv('train_data.csv',low_memory=False)

train_data_pd = train_data_pd.dropna(subset=['next_day_return'])
# 定义要排除的列
columns_to_exclude = ['adj_factor','popularity_ranking', 'limit', 'maturity', 'maturity_put_price', 'issue_size', 'high_stk', 'close_stk', 'conv_price', 'low_stk', 'open_stk','Unnamed: 0','rating','yy_rating','orgform','area','industry_1','industry_2','industry_3','list_date','conv_start_date','conv_end_date','is_call','datetime','code','trade_date','name','code_stk','name_stk','next_day_return','next_day_open','next_day_high','next_day_return_stop_win3','next_day_return_stop_win6']
columns_to_use = ['bias_5','pct_chg','pct_chg_5','open', 'high', 'low', 'close','vol',
                             'pct_chg_5_stk', 'vol_5','vol_stk',
                            'debt_to_assets']

# 使用列表推导式生成新的列名列表
new_columns = [col for col in train_data_pd.columns if col not in columns_to_exclude]
new_columns = columns_to_use
train_data= train_data_pd[new_columns]
column_means = train_data.mean()
# 填充NaN值为每列的均值
train_data = train_data.fillna(column_means)
# 生成因子数据
x = train_data

y=train_data_pd['next_day_return_stop_win3']
X_train, X_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=42)


rf = RandomForestRegressor(n_estimators=100, random_state=42,n_jobs=-1)

rf.fit(X_train, y_train)
# 保存模型
with open('model.pkl', 'wb') as file:
    pickle.dump(rf, file)

# 加载模型
with open('model.pkl', 'rb') as file:
    loaded_model = pickle.load(file)
# 4. 模型预测
y_pred = loaded_model.predict(X_test)

# 评估模型
mse = mean_squared_error(y_test, y_pred)
print(f"均方误差 (MSE): {mse}")

top_percentage = 0.2
num_stocks = int(len(y_pred) * top_percentage)
top_indices = np.argsort(y_pred)[-num_stocks:]

# 计算选中股票的实际收益率
selected_returns = y_test.iloc[top_indices]
portfolio_return = selected_returns.mean()
print(f"投资组合收益率: {portfolio_return}")

# 可视化预测结果与实际结果
plt.scatter(y_test, y_pred)
plt.xlabel('实际收益率')
plt.ylabel('预测收益率')
plt.title('实际收益率 vs 预测收益率')
plt.show()

