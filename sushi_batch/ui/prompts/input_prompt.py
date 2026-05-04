from prompt_toolkit import prompt
from prompt_toolkit.formatted_text.base import AnyFormattedText, StyleAndTextTuples
from prompt_toolkit.styles import BaseStyle, Style, merge_styles

from ...utils.console_utils import print_error
from ...utils.constants import CustomColor

def _get_default_style(success: bool = False) -> Style:
    """Return the default prompt style, with optional success message color."""
    message_color: str = CustomColor.SUCCESS if success else CustomColor.ACCENT
    return Style.from_dict({
        "message": message_color,
        "bottom-toolbar": f"fg:{CustomColor.BG_DARK} bg:{CustomColor.MUTED_LIGHTER}"
    })


def get(
    message: str = "New value: ",
    allow_empty: bool = False,
    nl_before: bool = False,
    success: bool = False,
    style: BaseStyle | None = None,
    bottom_toolbar: AnyFormattedText = None,
) -> str:
    """Prompt user for input."""
    _style: BaseStyle = (
        merge_styles([_get_default_style(success=success), style])
        if style
        else _get_default_style(success=success)
    )

    _message: StyleAndTextTuples = [("class:message", f"> {message}")]

    if nl_before and not message.strip().startswith("\n"):
        print()  
        
    while True:
        user_input: str = prompt(message=_message, style=_style, bottom_toolbar=bottom_toolbar)
        
        if not allow_empty and (user_input.isspace() or not user_input):
            print_error("Input cannot be empty!", wait=False, nl_after=True)
        else:            
            return user_input
