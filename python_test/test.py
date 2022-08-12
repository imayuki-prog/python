
test = True
count = 0

while test:
  count += 2

  print(count)

  if count > 8:
    test = False



test = False
count = 0

while not test:
  count += 2

  print(count)

  if count > 8:
    test = True