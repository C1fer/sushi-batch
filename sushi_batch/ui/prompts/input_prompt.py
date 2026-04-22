
from prompt_toolkit import prompt
from prompt_toolkit.styles import Style, merge_styles 

from ...utils import constants
from ...utils.console_utils import print_error


def _get_default_style(success=False):
    """Return the default prompt style, with optional success message color."""
    message_color = constants.COLOR_SUCCESS if success else constants.COLOR_ACCENT
    return Style.from_dict({
        "message": message_color,
        "bottom-toolbar": f"fg:{constants.COLOR_BG_DARK} bg:{constants.COLOR_MUTED_LIGHTER}"
    })


def get(message="New value: ", allow_empty=False, nl_before=False, success=False, **kwargs):
    """Prompt user for input."""
    caller_style = kwargs.pop("style", None)
    default_style = _get_default_style(success=success)
    kwargs["style"] = merge_styles([default_style, caller_style]) if caller_style else default_style

    _message = [("class:message", f"> {message}")]

    if nl_before and not message.strip().startswith("\n"):
        print()  
        
    while True:
        user_input = prompt(_message, **kwargs)
        
        if not allow_empty and (user_input.isspace() or not user_input):
            print_error("Input cannot be empty!\n", False)
        else:            
            return user_input
