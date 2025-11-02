import os
from time import sleep

from colorama import Fore, Style, init

# Store Fore and Style attributes to enable direct access from other modules
init(autoreset=True)
fore = Fore
style_reset = Style.RESET_ALL


def _print_colored(message, color, nl_before=False):
    """Small helper to print a colored message, optionally prefixed by a newline."""
    if nl_before:
        print()
    print(f"{color}{message}{style_reset}")


def print_header(message):
    _print_colored(message, fore.CYAN)


def print_subheader(message):
    _print_colored(message, fore.YELLOW, nl_before=True)


def print_error(message, wait=True):
    _print_colored(message, fore.LIGHTRED_EX)
    if wait:
        sleep(1)


def print_success(message, wait=True):
    _print_colored(message, fore.LIGHTGREEN_EX, nl_before=True)
    if wait:
        sleep(1)


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def show_menu_options(options):
    print()
    for key, val in options.items():
        print(f"{key}) {val}")


def confirm_action(prompt="Are you sure? (Y/N): "):
    """Prompt user for a yes/no confirmation."""
    while True:
        confirm = input(f"{fore.CYAN}{prompt}").upper()
        match confirm:
            case "Y":
                return True
            case "N":
                return False
            case _:
                print_error("Wrong input!\n", False)


def get_choice(start, end, prompt="Select an option: "):
    """Prompt user to select an option within a specified range."""
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
