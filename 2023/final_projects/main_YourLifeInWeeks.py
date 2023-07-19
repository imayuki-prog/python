age = input("What is your current age? ")
left_age = 90 - int(age)
days = int(left_age * 365)
weeks = int(left_age * 52)
months = int(left_age * 12)

message = f"You have {days} days, {weeks} weeks, and {months} months left."
print(message)