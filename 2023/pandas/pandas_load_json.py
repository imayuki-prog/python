import pandas as pd
import csv
from pathlib import Path

my_json = Path("/Users/yukiimazawa/Programming/python/2023/pandas/data.js")
df = pd.read_json(my_json.resolve())
print(df)

print(df.to_string())
# use to_string() to print the entire DataFrame

