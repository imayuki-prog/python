print("Welcome to the tip calculator!!")

total_bill = float(input("What was the total bill? $"))
print(total_bill)

split_people = float(input("How many people to split the bill? "))
print(split_people)

tip_percentage = float(input("What percentage tip would you like to give? 10, 12, 15 or more %?"))
print(tip_percentage)

tip = (tip_percentage / 100) + 1
total = total_bill * tip
splited = round(total / split_people,2)

print(f"Each person should pay ${splited}.")
