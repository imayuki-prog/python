import pandas as pd
import csv
from pathlib import Path

my_csv = Path("/Users/yukiimazawa/Programming/python/2023/pandas/data.csv")
df = pd.read_csv(my_csv.resolve(), sep=',')

####################################
x = df["Calories"].mean()
df["Calories"].fillna(x, inplace = True)
print(df.to_string())
# mean() = the average values(the sum of all values divided by number of values.)
####################################
x = df["Calories"].median()
df["Calories"].fillna(x, inplace = True)
print(df.to_string())
# median() = the value in the middle, after you have sorted all values ascending.
####################################
x = df["Calories"].mode()[0]
df["Calories"].fillna(x, inplace = True)
print(df.to_string())
# mode() = the value that appears most frequently
####################################
