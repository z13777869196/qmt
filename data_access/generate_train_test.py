
from _datetime import datetime
import pandas as pd
from sklearn.preprocessing import LabelEncoder

add_return_pd = pd.read_csv('data/add_return.csv', low_memory=False)
label_encoder = LabelEncoder()
add_return_pd['industry_1_label']  = label_encoder.fit_transform(add_return_pd['industry_1'])
add_return_pd['industry_2_label']  = label_encoder.fit_transform(add_return_pd['industry_2'])
add_return_pd['industry_3_label']  = label_encoder.fit_transform(add_return_pd['industry_3'])
add_return_pd['rating_label']  = label_encoder.fit_transform(add_return_pd['rating'])
add_return_pd['org_form_label']  = label_encoder.fit_transform(add_return_pd['orgform'])
add_return_pd['area_label']  = label_encoder.fit_transform(add_return_pd['area'])

add_return_pd['datetime'] = add_return_pd.apply(lambda x: datetime.strptime(x['trade_date'], '%Y-%m-%d'), axis=1)
# 数居范围
train_data_start = datetime(2020, 1, 1)

train_data_end =datetime(2024, 6, 1)
target_key='next_day_return_stop_win3'
add_return_pd = add_return_pd.dropna(subset=[target_key])
add_return_pd.to_csv('data/all_data.csv', index=False)
# 生成训练数据
train_data_pd= add_return_pd[add_return_pd['datetime']<=train_data_end]
train_data_pd = train_data_pd[train_data_pd['datetime']>=train_data_start]
train_data_pd.to_csv('data/train_data.csv', index=False)

# 生成测试数据
test_data_pd = add_return_pd[add_return_pd['datetime']>train_data_end]
test_data_pd.to_csv('data/test_data.csv', index=False)



test_data_pd_2 = add_return_pd[add_return_pd['datetime']<train_data_start]
test_data_pd_2.to_csv('data/test_data_2.csv', index=False)