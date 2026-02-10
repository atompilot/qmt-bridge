import os
from xtquant import xtdata

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
os.makedirs(DATA_DIR, exist_ok=True)

STOCK_LIST = ['000001.SZ']
FIELD_LIST = ['open', 'high', 'low', 'close', 'volume']

PERIOD = '1d'
COUNT = 5

# 下载数据到本地缓存
for stock in STOCK_LIST:
    xtdata.download_history_data(stock, period=PERIOD, start_time='', end_time='')

# 拉取行情数据
data = xtdata.get_market_data(
    field_list=FIELD_LIST,
    stock_list=STOCK_LIST,
    period=PERIOD,
    count=COUNT
)

# 按股票代码导出CSV：每个股票一个文件，行为日期，列为字段
for stock in STOCK_LIST:
    rows = {}
    for field in FIELD_LIST:
        df = data[field]
        if stock in df.index:
            for date, value in df.loc[stock].items():
                rows.setdefault(date, {})[field] = value

    if not rows:
        print(f'{stock} 无数据，跳过')
        continue

    import pandas as pd
    df_out = pd.DataFrame.from_dict(rows, orient='index')
    df_out.index.name = 'date'
    df_out = df_out[FIELD_LIST]

    filepath = os.path.join(DATA_DIR, f'{stock}.csv')
    df_out.to_csv(filepath)
    print(f'{stock} -> {filepath}  ({len(df_out)} 条)')