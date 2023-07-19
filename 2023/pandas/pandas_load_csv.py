import pandas as pd
import csv
from pathlib import Path

my_csv = Path("/Users/yukiimazawa/Programming/python/2023/pandas/data.csv")
df = pd.read_csv(my_csv.resolve(), sep=',')
print(df)
print(df.to_string())
print(pd.options.display.max_rows)
pd.options.display.max_rows = 10
df = pd.read_csv(my_csv.resolve(), sep=',')
print(df)

