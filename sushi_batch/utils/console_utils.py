import os
from time import sleep

from colorama import Fore, Style, init
from yaspin.core import Yaspin

from .constants import DynamicMenuItem, MenuItem

type ConsoleColor = int

# Store Fore and Style attributes to enable direct access from other modules
init(autoreset=True)
fore = Fore
style_reset: ConsoleColor = Style.RESET_ALL

def _print_colored(message: str, color: ConsoleColor, nl_before: bool = False, nl_after: bool = False) -> None:
    """Small helper to print a colored message, optionally prefixed by a newline."""
    _to_print = f"{color}{message}{style_reset}"
    if nl_before:
        _to_print = f"\n{_to_print}"
    if nl_after:
        _to_print = f"{_to_print}\n"
    print(_to_print)


def print_header(message: str, nl_before: bool = False, nl_after: bool = False) -> None:
    _print_colored(message, fore.CYAN, nl_before=nl_before, nl_after=nl_after)


def print_subheader(message: str, nl_before: bool = True, nl_after: bool = False) -> None:
    _print_colored(message, fore.YELLOW, nl_before=nl_before, nl_after=nl_after)


def print_error(message: str, wait: bool = True, nl_before: bool = False, nl_after: bool = False) -> None:
    _print_colored(message, fore.LIGHTRED_EX, nl_before=nl_before, nl_after=nl_after)
    if wait:
        sleep(1)

def print_warning(message: str, wait: bool = True, nl_before: bool = False, nl_after: bool = False) -> None:
    _print_colored(message, fore.LIGHTYELLOW_EX, nl_before=nl_before, nl_after=nl_after)
    if wait:
        sleep(1)


def print_success(message: str, wait: bool = True, nl_before: bool = True, nl_after: bool = False) -> None:
    _print_colored(message, fore.LIGHTGREEN_EX, nl_before=nl_before, nl_after=nl_after)
    if wait:
        sleep(1)

def get_formatted_install_status(tool_name: str, is_installed: bool, installed_label: str="Installed", not_found_label: str="Not Found") -> str:
    """Get a formatted string indicating the installation status of an external application."""
    status: str = installed_label if is_installed else not_found_label
    color: int = fore.LIGHTGREEN_EX if is_installed else fore.LIGHTRED_EX
    return f"{fore.LIGHTBLACK_EX}{tool_name}: {color}{status}{style_reset}"

def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")

def try_print_spinner_message(message: str, spinner: Yaspin | None = None) -> None:
    """Try to print a message to the spinner if it is provided, otherwise print the message to the console."""
    try:
        if isinstance(spinner, Yaspin):
            spinner.write(message)
        else:
            print(message)
    except Exception:
        print(message)

def print_help_text(subheader: str, description: str | tuple[str, ...], nl_after_subheader: bool = True) -> None:
    """Print help text with a subheader and description."""
    print_subheader(subheader, nl_after=nl_after_subheader)
    if isinstance(description, tuple):
        for text in description:
            print(text)
    else:
        print(description)


def get_visible_options(options: list[MenuItem | DynamicMenuItem], validations: dict[str, bool]) -> list[MenuItem]:
    """Return the visible options from the given options based on the validations."""
    visible_options: list[MenuItem] = []
    for opt in options:
        match opt:
            case (choice_id, label):
                visible_options.append((choice_id, label))
            case (choice_id, label, is_visible_fn):
                if is_visible_fn(validations):
                    visible_options.append((choice_id, label))
    return visible_options
