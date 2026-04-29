import os
from time import sleep

from colorama import Fore, Style, init

# Store Fore and Style attributes to enable direct access from other modules
init(autoreset=True)
fore = Fore
style_reset = Style.RESET_ALL


def _print_colored(message, color, nl_before=False, nl_after=False):
    """Small helper to print a colored message, optionally prefixed by a newline."""
    _to_print = f"{color}{message}{style_reset}"
    if nl_before:
        _to_print = f"\n{_to_print}"
    if nl_after:
        _to_print = f"{_to_print}\n"
    print(_to_print)


def print_header(message, nl_before=False, nl_after=False):
    _print_colored(message, fore.CYAN, nl_before=nl_before, nl_after=nl_after)


def print_subheader(message, nl_before=True):
    _print_colored(message, fore.YELLOW, nl_before=nl_before)


def print_error(message, wait=True, nl_before=False):
    _print_colored(message, fore.LIGHTRED_EX)
    if wait:
        sleep(1)

def print_warning(message, wait=True, nl_before=False):
    _print_colored(message, fore.LIGHTYELLOW_EX, nl_before=nl_before)
    if wait:
        sleep(1)


def print_success(message, wait=True, nl_before=True):
    _print_colored(message, fore.LIGHTGREEN_EX, nl_before=nl_before)
    if wait:
        sleep(1)

def get_formatted_install_status(tool_name, is_installed, installed_label="Installed", not_found_label="Not Found"):
    status = installed_label if is_installed else not_found_label
    color = fore.LIGHTGREEN_EX if is_installed else fore.LIGHTRED_EX
    return f"{fore.LIGHTBLACK_EX}{tool_name}: {color}{status}{style_reset}"

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

def try_print_spinner_message(message, spinner=None):
    try:
        if spinner:
            spinner.write(message)
        else:
            print(message)
    except Exception:
        print(message)

def print_help_text(subheader, description):
    print_subheader(subheader)
    if isinstance(description, tuple):
        for text in description:
            print(text)
    else:
        print(description)