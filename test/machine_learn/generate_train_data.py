import pandas as pd
from datetime import datetime
add_return_pd = pd.read_csv('add_return.csv',low_memory=False)
add_return_pd['datetime'] = pd.to_datetime(add_return_pd.trade_date)
train_data= add_return_pd[add_return_pd['datetime']<=datetime(2023, 12, 30)]
train_data = train_data[train_data['datetime']>datetime(2019, 1, 1)]
train_data.to_csv('train_data.csv',index=False)
