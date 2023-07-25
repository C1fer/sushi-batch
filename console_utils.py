import os
from colorama import Fore, Style


# Clear command line screen
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear') 


# Ask for user confirmation
def confirm_action(prompt = f"{Fore.LIGHTWHITE_EX}Are you sure? (Y/N): "):
    while True:
        confirm = input(prompt).upper()
        match confirm:
            case "Y":
                return True

            case "N":
                return False
            case others:
                print(f"{Fore.LIGHTRED_EX}Wrong input!\n")
    return True


# Get option selected by user
def get_choice(options_range):
    while True:
        try:
            choice = int(input(f"\n{Fore.LIGHTBLACK_EX}Select an option: "))
            if choice in options_range:
                Style.RESET_ALL
                return choice
            else:
                print(f"{Fore.LIGHTRED_EX}Invalid choice! Please select a valid option.\n")
        except ValueError:
            print(f"{Fore.LIGHTRED_EX}Invalid choice! Please select a valid option.\n")
    
