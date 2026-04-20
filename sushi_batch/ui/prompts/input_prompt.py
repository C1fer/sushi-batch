
from prompt_toolkit import prompt
from prompt_toolkit.styles import Style, merge_styles 

from ...utils import constants
from ...utils.console_utils import print_error

DEFAULT_STYLE = Style.from_dict({
    "message": constants.COLOR_ACCENT,
    "bottom-toolbar": f"fg:{constants.COLOR_BG_DARK} bg:{constants.COLOR_MUTED_LIGHTER}"
})


def get(message="New value: ", allow_empty=False, **kwargs):
    """Prompt user for input."""
    caller_style = kwargs.pop("style", None)
    kwargs["style"] = merge_styles([DEFAULT_STYLE, caller_style]) if caller_style else DEFAULT_STYLE

    _message = [("class:message", f"> {message}")]

    
    while True:
        user_input = prompt(_message, **kwargs)
        
        if not allow_empty and (user_input.isspace() or not user_input):
            print_error("Input cannot be empty!\n", False)
        else:            
            return user_input
