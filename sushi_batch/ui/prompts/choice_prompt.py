from prompt_toolkit.shortcuts import choice
from prompt_toolkit.styles import BaseStyle, Style, merge_styles
from prompt_toolkit.formatted_text.base import AnyFormattedText, StyleAndTextTuples

from ...utils.constants import CustomColor, BOTTOM_TOOLBAR_STATS_STYLES, SelectableOption


DEFAULT_STYLE: Style = Style.from_dict({
    "frame.border": CustomColor.MUTED,
    "selected-option": f"fg:{CustomColor.ACCENT} bold",
    **BOTTOM_TOOLBAR_STATS_STYLES
})

def get(
    message: str = "Select an option: ",
    options: list[SelectableOption] | None = None,
    nl_before: bool = True,
    nl_after: bool = True,
    style: BaseStyle | None = None,
    bottom_toolbar: AnyFormattedText | StyleAndTextTuples = None,
    mouse_support: bool = True,
    show_frame: bool = False,
    default_option: int | None = None,
) -> int:
    """Use prompt_toolkit to display a choice prompt with the given options."""
    normalized_options: list[SelectableOption] = options if options is not None else []

    _style: BaseStyle = (
        merge_styles([DEFAULT_STYLE, style])
        if style
        else DEFAULT_STYLE
    )

    if nl_before and not message.strip().startswith("\n"):
        print()

    user_choice: int = choice(
        message,
        options=normalized_options,
        mouse_support=mouse_support,
        style=_style,
        bottom_toolbar=bottom_toolbar,
        show_frame=show_frame,
        default=default_option,
    )

    if nl_after and not message.strip().endswith("\n") and not show_frame:
        print()
        
    return user_choice