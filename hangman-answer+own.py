
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

end_of_game = False
word_list = ["ardvark", "baboon", "camel"]
chosen_word = random.choice(word_list)
word_length = len(chosen_word)

#TODO-1: - Create a variable called 'lives' to keep track of the number of lives left. 
#Set 'lives' to equal 6.

#Testing code
print(f'Pssst, the solution is {chosen_word}.')

blank = []
for b in chosen_word:
  blank += "_"


miss = 0
miss_count = 7

while not end_of_game:
  print(blank) 
  miss = 0
  guess = input("Guess a letter: ").lower()
  
  for position in range(word_length):
    
    letter = chosen_word[position]
    
    if guess == letter:
      blank[position] = letter

    else:
      miss += 1
      
  if miss == len(blank):
    miss_count -= 1  
    print(stages[miss_count])  
    miss = 0
    
    if miss_count == 0:
      print("game over") 
      break
    
  elif "_" not in blank:
    end_of_game = True
    print(blank)
    print("You win")