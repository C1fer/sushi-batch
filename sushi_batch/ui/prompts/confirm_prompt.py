
from prompt_toolkit import prompt
from prompt_toolkit.styles import Style, merge_styles
from prompt_toolkit.cursor_shapes import CursorShape

from ...utils import constants
from ...utils.console_utils import print_error

DEFAULT_STYLE = { **constants.BOTTOM_TOOLBAR_STATS_STYLES}

def get(message="Are you sure?", suffix=" (Y/N): ", nl_before=False, nl_after=False, destructive=False, **kwargs):
    """Prompt user for a yes/no confirmation."""
    kwargs.setdefault("cursor", CursorShape.BLOCK)
    caller_style = kwargs.pop("style", None)

    _color = constants.COLOR_DESTRUCTIVE if destructive else constants.COLOR_ACCENT
    DEFAULT_STYLE["message"] = f"fg:{_color} bold"

    kwargs["style"] = (
        merge_styles([Style.from_dict(DEFAULT_STYLE), caller_style])
        if caller_style
        else Style.from_dict(DEFAULT_STYLE)
    )

    _message = [("class:message", f"> {message}{suffix}")]


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
