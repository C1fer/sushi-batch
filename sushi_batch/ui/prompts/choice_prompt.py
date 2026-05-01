from typing import Sequence
from prompt_toolkit.shortcuts import choice
from prompt_toolkit.styles import BaseStyle, Style, merge_styles
from prompt_toolkit.formatted_text.base import AnyFormattedText

from ...utils.constants import CustomColor, BOTTOM_TOOLBAR_STATS_STYLES

type ChoiceOptions = Sequence[tuple[int | str, AnyFormattedText]]

DEFAULT_STYLE: Style = Style.from_dict({
    "frame.border": CustomColor.MUTED,
    "selected-option": f"fg:{CustomColor.ACCENT} bold",
    **BOTTOM_TOOLBAR_STATS_STYLES
})

def _validate_choice_options(options):
    """Validate that options are in the correct format for choice prompt."""
    if isinstance(options, dict):
        return list(options.items())
    elif isinstance(options, (list, tuple)):
        if all(isinstance(opt, (list, tuple)) and len(opt) == 2 for opt in options):
            return options
        else:
            raise ValueError("Options list must contain (value, label) pairs.")
    else:
        raise TypeError("Options must be a dict or a list/tuple of (value, label) pairs.")
    
def get(
    message: str = "Select an option: ",
    options: ChoiceOptions | None = None,
    nl_before: bool = True,
    nl_after: bool = True,
    style: BaseStyle | None = None,
    bottom_toolbar: AnyFormattedText = None,
    mouse_support: bool = True,
    show_frame: bool = False,
) -> int:
    """Use prompt_toolkit to display a choice prompt with the given options."""
    normalized_options: ChoiceOptions = options if options is not None else _validate_choice_options(options)
    _validate_choice_options(normalized_options)

    _style: BaseStyle = (
        merge_styles([DEFAULT_STYLE, style])
        if style
        else DEFAULT_STYLE
    )

    if nl_before and not message.strip().startswith("\n"):
        print()

    user_choice = choice(
        message,
        options=normalized_options,
        mouse_support=mouse_support,
        style=_style,
        bottom_toolbar=bottom_toolbar,
        show_frame=show_frame,
    )

    if nl_after and not message.strip().endswith("\n") and not show_frame:
        print()
        
    return user_choice