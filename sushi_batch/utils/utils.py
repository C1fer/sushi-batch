from os import name
from pathlib import Path
import subprocess
import sys
from importlib.util import find_spec
from typing import Any, Callable

from ..ui.prompts import confirm_prompt
from . import console_utils as cu


def is_app_installed(app_name: str) -> bool:
    """Check if an application is installed by checking if the executable is in the PATH or in the working directory."""
    if is_app_env_var(app_name):
        return True
    
    # If running on Windows, check if executable is inside working directory 
    elif name == "nt" and Path(Path.cwd(), f"{app_name}.exe").exists(): 
        return True
    
    return False


def is_app_env_var(app: str) -> bool:
    """Check if an application is installed by checking if the executable is in the PATH or in the working directory."""
    try:
        subprocess.run(app, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except OSError:
        return False
    else:
        return True
    

def check_required_packages() -> None:
    """Check if all required packages are installed."""
    packages: list[str] = ["art", "colorama", "sushi", "prettytable", "yaspin", "prompt_toolkit"]
    for pkg in packages:
        if not find_spec(pkg):
            print(f"\033[91mPackage {pkg} is not installed. Install all dependencies before running the tool\033[00m")
            sys.exit(1)


def _confirm_abort_after_interrupt(message: str = "Are you sure you want to cancel this operation?") -> bool:
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

def interrupt_signal_handler(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to handle KeyboardInterrupt gracefully in interactive functions."""
    def wrapper(*args: Any, **kwargs: Any) -> Any:
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


def pop_many(dct: dict[str, Any], *keys: str) -> None:
    for key in keys:
        dct.pop(key, None)