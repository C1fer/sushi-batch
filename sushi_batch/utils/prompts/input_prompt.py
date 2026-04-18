
from prompt_toolkit import prompt
from prompt_toolkit.styles import Style 

from ..constants import COLOR_ACCENT
from ..console_utils import print_error

DEFAULT_STYLE = Style.from_dict({
    "message": COLOR_ACCENT 
})


def get(message="New value: ", allow_empty=False, **kwargs):
    """Prompt user for input."""
    _message = [("class:message", f"{message}")]
    
    while True:
        user_input = prompt(_message, style=DEFAULT_STYLE, **kwargs)
        
        if not allow_empty and (user_input.isspace() or not user_input):
            print_error("Input cannot be empty!\n", False)
        else:            
            return user_input
