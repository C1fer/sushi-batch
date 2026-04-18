
from prompt_toolkit import prompt
from prompt_toolkit.styles import Style 

from ..constants import COLOR_ACCENT
from ..console_utils import print_error

DEFAULT_STYLE = Style.from_dict({
    "message": COLOR_ACCENT 
})


def get(message="Are you sure?", suffix=" (Y/N): ", **kwargs):
    """Prompt user for a yes/no confirmation."""
    _message = [("class:message", f"{message}{suffix}")]
    
    while True:
        user_input = prompt(_message, style=DEFAULT_STYLE, **kwargs).upper()
        match user_input:
            case "Y":
                return True
            case "N":
                return False
            case _:
                print_error("Wrong input!\n", False)