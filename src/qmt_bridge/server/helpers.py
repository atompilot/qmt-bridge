"""QMT Bridge — data conversion helpers."""

import numpy as np
import pandas as pd


def _numpy_to_python(obj):
    """Recursively convert numpy types in a nested structure to Python types."""
    if isinstance(obj, dict):
        return {k: _numpy_to_python(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_numpy_to_python(i) for i in obj]
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    return obj


def _market_data_to_records(
    raw: dict, stock_list: list[str], field_list: list[str]
) -> dict[str, list[dict]]:
    """Convert xtdata.get_market_data() result to JSON-friendly records.

    raw is {field: DataFrame} where each DataFrame has stocks as rows and
    timestamps as columns.  We pivot into {stock: [{date, field1, field2, ...}]}.
    """
    result: dict[str, list[dict]] = {}
    for stock in stock_list:
        rows: dict[str, dict] = {}
        for field in field_list:
            df = raw.get(field)
            if df is None:
                continue
            if stock in df.index:
                for date, value in df.loc[stock].items():
                    entry = rows.setdefault(str(date), {"date": str(date)})
                    entry[field] = value.item() if hasattr(value, "item") else value
        result[stock] = list(rows.values())
    return result


def _dataframe_dict_to_records(data: dict) -> dict[str, list[dict]]:
    """Convert {stock: DataFrame} format (get_market_data_ex / get_local_data return value).

    Returns {stock: [row_dict, ...]} where each row_dict includes all columns.
    """
    result: dict[str, list[dict]] = {}
    for stock, df in data.items():
        if isinstance(df, pd.DataFrame) and not df.empty:
            records = df.reset_index().to_dict(orient="records")
            result[stock] = [_numpy_to_python(r) for r in records]
        else:
            result[stock] = []
    return result


def _financial_data_to_records(data: dict) -> dict:
    """Convert {stock: {table: DataFrame}} format (get_financial_data return value).

    Returns {stock: {table: [row_dict, ...]}}.
    """
    result: dict = {}
    for stock, tables in data.items():
        stock_data: dict = {}
        if isinstance(tables, dict):
            for table_name, df in tables.items():
                if isinstance(df, pd.DataFrame) and not df.empty:
                    records = df.reset_index().to_dict(orient="records")
                    stock_data[table_name] = [_numpy_to_python(r) for r in records]
                else:
                    stock_data[table_name] = []
        result[stock] = stock_data
    return result
