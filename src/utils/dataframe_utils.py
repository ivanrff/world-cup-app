import pandas as pd

def to_br_timezone(column):
    converted_col = pd.to_datetime(column).dt.tz_convert(
    "America/Sao_Paulo").dt.tz_localize(None)

    return converted_col