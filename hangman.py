#Step 2

import random
word_list = ["aardvark", "baboon", "camel"]
chosen_word = random.choice(word_list)
list_chosen_word = list(chosen_word)
#Testing code
print(f'Pssst, the solution is {chosen_word}.')

blank = ""
for b in range(0, (len(chosen_word))):
  blank += "_"

blank_list = list(blank)

guess = input("Guess a letter: ").lower()

for letter in chosen_word:
    if letter == guess:
        print("Right")
    else:
        print("Wrong")

