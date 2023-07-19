import pandas as pd
import csv
from pathlib import Path

my_csv = Path("/Users/yukiimazawa/Programming/python/2023/pandas/data.csv")
df = pd.read_csv(my_csv.resolve(), sep=',')

####################################
new_df = df.dropna()
#^ .dropna() returns Data Frame with no empty cells.
print(new_df.to_string())
####################################
df.dropna(inplace = True)
#^ .dropna(inplace = True) remove all rows with NULL values.

####################################
df.fillna(9999999, inplace = True)
#^ .fillna( , inplace = True) replaces NULL values with the number " "
print(df.to_string())
####################################
df["Calories"].fillna(88888, inplace = True)
# ^ [" "].fillna( , inplace = True) Replaces NULL values in the " " columns with the number " "
print(df.to_string())