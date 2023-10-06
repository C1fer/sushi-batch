import os
import shutil
import subprocess
from time import sleep

from colorama import Fore, Style, init

# Store Fore and Style attributes to enable direct access from other modules
init(autoreset=True)
fore = Fore
style_reset = Style.RESET_ALL


# Clear command line screen
def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def print_header(message):
    return print(f"{fore.CYAN}{message}")


def print_subheader(message):
    return print(f"\n{fore.YELLOW}{message}")


def print_error(message, wait=True):
    print(f"{fore.LIGHTRED_EX}{message}")
    if wait:
        sleep(1)


def print_success(message):
    print(f"\n{fore.LIGHTGREEN_EX}{message}")
    sleep(1)


# Ask for user confirmation
def confirm_action(prompt="Are you sure? (Y/N): "):
    while True:
        confirm = input(f"{fore.CYAN}{prompt}").upper()
        match confirm:
            case "Y":
                return True
            case "N":
                return False
            case others:
                print_error("Wrong input!\n", False)


# Get option selected by user
def get_choice(start, end, prompt="Select an option: "):
    while True:
        try:
            choice = int(input(f"\n{fore.LIGHTBLACK_EX}{prompt}"))
        except ValueError:
            print_error("Invalid choice! Please select a valid option.", False)
        else:
            if choice in range(start, end + 1):
                print()
                return choice
            else:
                print_error("Invalid choice! Please select a valid option.", False)


# Show formatted menu options
def show_menu_options(options):
    print()
    for key, val in options.items():
        print(f"{key}) {val}")


# Check if specified app is installed
def is_app_installed(app_name):
    # Check if app is an enviroment variable
    if is_app_env_var(app_name):
        return True
    
    # If running on Windows, check if executable is inside working directory 
    elif os.name == "nt" and os.path.exists(os.path.join(os.getcwd(), f"{app_name}.exe")): 
        return True
    
    return False


# Run subprocess to check if app is on PATH env var
def is_app_env_var(app):
    try:
        subprocess.run(app, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except OSError as e:
        return False
    else:
        return True
    

def clear_logs(dirpath):
    try:
        for entry in os.listdir(dirpath):
            if entry in("Sushi Logs", "Merge Logs"):
                entry_path = os.path.join(dirpath, entry)
                shutil.rmtree(entry_path)  # Recursively delete the directory
    except OSError as e:
        print(e)