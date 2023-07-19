import pandas as pd

mydataset = {
  'cars': ["BMW", "Volvo", "Ford"],
  'passings': [3, 7, 2]
}

index = ["the first", "the second", "the third"]

myvar = pd.DataFrame(mydataset, index)

print(myvar)
