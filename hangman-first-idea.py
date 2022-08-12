

import random

stages = ['''
  +---+
  |   |
  O   |
 /|\  |
 / \  |
      |
=========
''', '''
  +---+
  |   |
  O   |
 /|\  |
 /    |
      |
=========
''', '''
  +---+
  |   |
  O   |
 /|\  |
      |
      |
=========
''', '''
  +---+
  |   |
  O   |
 /|   |
      |
      |
=========''', '''
  +---+
  |   |
  O   |
  |   |
      |
      |
=========
''', '''
  +---+
  |   |
  O   |
      |
      |
      |
=========
''', '''
  +---+
  |   |
      |
      |
      |
      |
=========
''']
word_list = ["aardvark", "baboon", "camel"]

chosen_word = random.choice(word_list)

list_chosen_word = list(chosen_word)

print(f'Pssst, the solution is {chosen_word}.')

#Generate blank list
blank =""
for b in range(len(chosen_word)):
  blank +="_"

blank_list = list(blank)

  
#User chosen letter 
print(blank_list)
guess = input("Guess a letter: ").lower()


#Loop to check wether correct or incorrect
miss_count = 6
word_count = -1
wrong_count = 0

while miss_count > -1:
  
  for letter in chosen_word:
    
    if letter == guess:
      word_count += 1
      blank_list[word_count] = guess
    else:
      word_count += 1
      wrong_count += 1
    
  if blank_list == list_chosen_word:
    print(blank_list)
    print("correct")
    break
  
  elif miss_count == 0:
    print(blank_list)
    print(stages[miss_count])
    print("game over")
    break

  elif wrong_count == len(chosen_word):
    print(stages[miss_count])
    print("miss")
    word_count = -1
    miss_count -= 1
    wrong_count = 0
    print(blank_list)
    guess = input("Guess a letter: ").lower()
    
  else:      
    print(word_count)
    word_count = -1
    wrong_count = 0
    print(blank_list)
    guess = input("Guess a letter: ").lower()