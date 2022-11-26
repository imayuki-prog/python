rock = '''
    _______
---'   ____)
      (_____)
      (_____)
      (____)
---.__(___)
'''

paper = '''
    _______
---'   ____)____
          ______)
          _______)
         _______)
---.__________)
'''

scissors = '''
    _______
---'   ____)____
          ______)
       __________)
      (____)
---.__(___)
'''

#Write your code below this line 👇
list = [rock, paper, scissors]
import random

player_choice = int(input("What do you choose? Type 0 for Rock, 1 for Paper or 2 for Scissors : "))

if player_choice >=3 or player_choice > 0:
    print("Unfortunately, this number is invalid.\nCould you type again?" )
else:
    print(list[player_choice])
  
    computer_choice = random.randint(0, 2)
    print("Computer choice: ")
    print(list[computer_choice])

    if player_choice == computer_choice:
       print("Draw")
    elif player_choice == 0 and computer_choice == 2:
       print("You win!")
    elif player_choice == 2 and computer_choice == 0:
       print("You lose!")
    elif player_choice > computer_choice:
       print("You win!")  
    elif player_choice < computer_choice:
       print("You lose!")