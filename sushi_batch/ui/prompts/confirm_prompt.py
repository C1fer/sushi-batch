
from prompt_toolkit import prompt
from prompt_toolkit.formatted_text.base import AnyFormattedText, StyleAndTextTuples
from prompt_toolkit.styles import BaseStyle, Style, merge_styles

from ...utils.console_utils import print_error
from ...utils.constants import BOTTOM_TOOLBAR_STATS_STYLES, CustomColor

def _get_default_style(destructive: bool = False) -> Style:
    color: str = CustomColor.DESTRUCTIVE if destructive else CustomColor.ACCENT
    return Style.from_dict({ 
        **BOTTOM_TOOLBAR_STATS_STYLES, 
        "message": f"fg:{color} bold"
    })

def get(
    message="Are you sure?",
    suffix: str = " (Y/N): ",
    nl_before: bool = False,
    nl_after: bool = False,
    destructive: bool = False,
    style: BaseStyle | None = None,
    bottom_toolbar: AnyFormattedText = None,
) -> bool:
    """Prompt user for a yes/no confirmation."""
    _style: BaseStyle = (
        merge_styles([_get_default_style(destructive=destructive), style])
        if style
        else _get_default_style(destructive=destructive)
    )
    
    _message: StyleAndTextTuples= [("class:message", f"> {message}{suffix}")]

    if nl_before and not message.strip().startswith("\n"):
        print()

    def _print_new_line_after():
        if nl_after and not message.strip().endswith("\n"):
            print()

    while True:
        user_input: str = prompt(message=_message, style=_style, bottom_toolbar=bottom_toolbar).upper()
        match user_input:
            case "Y":
                _print_new_line_after()
                return True
            case "N":
                _print_new_line_after()
                return False
            case _:
                print_error("Wrong input!", wait=False, nl_after=True)
