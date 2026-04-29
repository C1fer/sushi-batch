import os
import subprocess
import sys
from importlib.util import find_spec

from ..ui.prompts import confirm_prompt
from . import console_utils as cu


def is_app_installed(app_name):
    if is_app_env_var(app_name):
        return True
    
    # If running on Windows, check if executable is inside working directory 
    elif os.name == "nt" and os.path.exists(os.path.join(os.getcwd(), f"{app_name}.exe")): 
        return True
    
    return False


def is_app_env_var(app):
    try:
        subprocess.run(app, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except OSError:
        return False
    else:
        return True
    

def check_required_packages():
    _PACKAGES = ["art", "colorama", "sushi", "prettytable", "yaspin", "prompt_toolkit"]

    for pkg in _PACKAGES:
        if find_spec(pkg) is None:
            print(
                f"\033[91mPackage {pkg} is not installed. Install all dependencies before running the tool\033[00m"
            )
            sys.exit(1)


def _confirm_abort_after_interrupt(message = "Are you sure you want to cancel this operation?"):
    """Ask whether to cancel after Ctrl+C; keep prompting if interrupted again."""
    while True:
        try:
            return confirm_prompt.get(message=message, destructive=True, nl_before=True)
        except KeyboardInterrupt:
            cu.print_warning(
                "Interrupt received while awaiting confirmation. Press Y to cancel or N to resume.",
                nl_before=True,
                wait=False,
            )

def interrupt_signal_handler(func):
    """Decorator to handle KeyboardInterrupt gracefully in interactive functions."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyboardInterrupt:
            if _confirm_abort_after_interrupt():
                cu.print_success("Operation cancelled.", nl_before=True)
                exit(0)
            else:
                cu.print_warning("Resuming operation...", nl_before=True)
                return wrapper(*args, **kwargs)  # Restart the function
    return wrapper


def pop_many(dct, *keys):
    for key in keys:
        dct.pop(key, None)