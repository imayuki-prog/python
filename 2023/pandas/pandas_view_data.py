import pandas as pd
import csv
from pathlib import Path

my_csv = Path("/Users/yukiimazawa/Programming/python/2023/pandas/data.csv")
df = pd.read_csv(my_csv.resolve(), sep=',')

print(df.head())
print(df.tail())
print(df.info())