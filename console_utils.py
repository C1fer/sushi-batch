import os
from time import sleep
from collections import namedtuple
from colorama import init, Fore, Style


# Store Fore and Style attributes to enable direct access from other modules
init(autoreset=True)
fore = Fore
style_reset = Style.RESET_ALL

app_logo = " ____               _      _     ____          _          _         _____                _ \n/ ___|  _   _  ___ | |__  (_)   | __ )   __ _ | |_   ___ | |__     |_   _|  ___    ___  | |\n\\___ \\ | | | |/ __|| '_ \\ | |   |  _ \\  / _` || __| / __|| '_ \\      | |   / _ \\  / _ \\ | |\n ___) || |_| |\\__ \\| | | || |   | |_) || (_| || |_ | (__ | | | |     | |  | (_) || (_) || |\n|____/  \\__,_||___/|_| |_||_|   |____/  \\__,_| \\__| \\___||_| |_|     |_|   \\___/  \\___/ |_|\n                                                                                           \n"


# Clear command line screen
def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def print_header(message):
    return print(f"{fore.CYAN}{message}")


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
def get_choice(start=1, end=None, prompt="Select an option: "):
    while True:
        try:
            choice = int(input(f"\n{fore.LIGHTBLACK_EX}{prompt}"))
            if choice in range(start, end + 1):
                return choice
            else:
                print_error("Invalid choice! Please select a valid option.", False)
        except ValueError:
            print_error("Invalid choice! Please select a valid option.", False)


# Show menu options
def show_menu_options(options):
    print("")
    for key, val in options.items():
        print(f"{key}) {val}")


# Look for ffmpeg binary in PATH env var and working directory
def is_ffmpeg_installed():
    # Check if FFmpeg is set on PATH
    if os.environ.get("PATH").find("ffmpeg") != -1:
        return True

    # If FFmpeg is not an enviroment variable, look for the binary in working directory
    ffmpeg_bin = ("ffmpeg.exe" if os.name == "nt" else "ffmpeg")  
    ffmpeg_path = os.path.join(os.getcwd(), ffmpeg_bin)

    if os.path.exists(ffmpeg_path):
        return True

    # If FFmpeg is not found, return false
    return False