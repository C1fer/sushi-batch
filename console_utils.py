import os

# Clear command line screen
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear') 


# Confirm choice
def confirm_action(prompt ="\nAre you sure? (Y/N): "):
    while True:
        confirm = input(prompt).upper()
        match confirm:
            case "Y":
                return True
            case "N":
                return False
            case others:
                print(f"{Fore.LIGHTRED_EX}Wrong input!\n")


# Get user choice
def get_choice(options_range):
    while True:
        try:
            choice = int(input("\nSelect an option: "))
            if choice in options_range:
                return choice
            else:
                print(f"{Fore.LIGHTRED_EX}Invalid choice! Please select a valid option.\n")
        except ValueError:
            print(f"{Fore.LIGHTRED_EX}Invalid choice! Please select a valid option.\n")
    
