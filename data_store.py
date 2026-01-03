import pandas as pd
import os
import threading

DATA_FILE = "data.xlsx"

_df_cache = None
_file_mtime = None
_lock = threading.Lock()


def load_data():
    global _df_cache, _file_mtime

    if not os.path.exists(DATA_FILE):
        return pd.DataFrame()

    mtime = os.path.getmtime(DATA_FILE)

    # baca ulang hanya jika file berubah
    if _df_cache is None or _file_mtime != mtime:
        with _lock:
            df = pd.read_excel(DATA_FILE, dtype=str, engine="openpyxl")
            df = df.fillna("")
            _df_cache = df
            _file_mtime = mtime

    return _df_cache.copy()


def save_data(df):
    global _df_cache, _file_mtime
    with _lock:
        df.to_excel(DATA_FILE, index=False, engine="openpyxl")
        _df_cache = df.copy()
        _file_mtime = os.path.getmtime(DATA_FILE)


def clear_cache():
    global _df_cache, _file_mtime
    _df_cache = None
    _file_mtime = None
