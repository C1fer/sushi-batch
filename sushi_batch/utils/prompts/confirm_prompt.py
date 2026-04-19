
from prompt_toolkit import prompt
from prompt_toolkit.styles import Style 
from prompt_toolkit.cursor_shapes import CursorShape

from ..constants import COLOR_ACCENT, COLOR_DESTRUCTIVE
from ..console_utils import print_error

def get(message="Are you sure?", suffix=" (Y/N): ", nl_before=False, nl_after=False, destructive=False, **kwargs):
    """Prompt user for a yes/no confirmation."""
    _message = [("class:message", f"> {message}{suffix}")]
    _color = COLOR_DESTRUCTIVE if destructive else COLOR_ACCENT

    kwargs.setdefault("style", Style([("message", f"fg:{_color} bold")]))
    kwargs.setdefault("cursor", CursorShape.BLOCK)
   
    if nl_before and not message.strip().startswith("\n"):
        print()

    def _print_new_line_after():
        if nl_after and not message.strip().endswith("\n"):
            print()

    while True:
        user_input = prompt(_message, **kwargs).upper()
        match user_input:
            case "Y":
                _print_new_line_after()
                return True
            case "N":
                _print_new_line_after()
                return False
            case _:
                print_error("Wrong input!\n", False)
