introduction = "Welcome to the tip calculator."
print(introduction)

total_bill = float(input("What was the total bill? $"))
tip = float(input("What percentage tip would you like to give? 10, 12 or 15? "))
ppl = float(input("How many people to split the bill? "))

tip_percents = tip / 100
tip_total = total_bill + (total_bill * tip_percents)
each = float(round(tip_total / ppl, 2))

message = f"Each person should pay ${each}"

print(message)