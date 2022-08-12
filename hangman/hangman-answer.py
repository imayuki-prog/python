#Step 5

import random
from hangman_art import stages 
from hangman_art import logo
from hangman_words import word_list


print("Welcome to")
print(logo)
chosen_word = random.choice(word_list)
word_length = len(chosen_word)

end_of_game = False
lives = 6


#Testing code
#print(f'Pssst, the solution is {chosen_word}.')


#Create blanks
display = []
for _ in range(word_length):
    display += "_"
player_chosen_words = []


#Structure of game
while not end_of_game:
  
    print("")
    print(display)
    guess = input("[Guess a letter]: ").lower()
  
    if guess in player_chosen_words:
      print("[You have already guessed this letter].")
    player_chosen_words += guess
  
    #Check guessed letter
    for position in range(word_length):
        letter = chosen_word[position]
        #print(f"Current position: {position}\n Current letter: {letter}\n Guessed letter: {guess}")
        if letter == guess:
            display[position] = letter

    #Check if user is wrong.
    if guess not in chosen_word:
        print("[It's not in the word.]")
        lives -= 1
        if lives == 0:
            end_of_game = True
            print(f'[You lose. Answer is {chosen_word}.]')

    #Join all the elements in the list and turn it into a String.
    print(f"{' '.join(display)}")

    #Check if user has got all letters.
    if "_" not in display:
        end_of_game = True
        print("[You win.]")

  
    print(stages[lives])
  