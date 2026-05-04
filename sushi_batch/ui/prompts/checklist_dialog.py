from prompt_toolkit.shortcuts import checkboxlist_dialog
from prompt_toolkit.styles import BaseStyle, Style, merge_styles
from prompt_toolkit.formatted_text.base import StyleAndTextTuples

from ...utils.constants import CustomColor, SelectableOption

DEFAULT_TOOLBAR = "  Arrows: Move | Space/Mouse Click: Select | Tab: Actions | Enter: Confirm  \n\n"

DEFAULT_STYLE: Style = Style.from_dict({
    "dialog": f"bg:{CustomColor.BG_DARK}",
    "dialog frame.label": f"fg:{CustomColor.ACCENT} bold",
    "dialog frame.border": f"fg:{CustomColor.MUTED}",
    "dialog.body": f"fg:{CustomColor.TEXT} bg:{CustomColor.BG_DARK}",
    "button": f"fg:{CustomColor.ACCENT} bold",
    "button.focused": f"bg:{CustomColor.BG_DARKER} bold",
    "checkbox-list": f"fg:{CustomColor.MUTED}",
    "checkbox": "",
    "checkbox-checked": f"fg:{CustomColor.ACCENT}",
    "checkbox-selected": "bold",
    "checkbox-checked-selected": f"fg:{CustomColor.ACCENT}",
    "selected": "bold",
    "message": f"fg:{CustomColor.TEXT}",
    "instructions": f"fg:{CustomColor.MUTED} bg:{CustomColor.BG_DARKER} bold",
})

def get(
    title: str = "",
    message: str = "Select options: ",
    options: list[SelectableOption] | None = None,
    style: Style | None = None,
) -> list[int]:
    """Prompt user for a checklist selection."""
    _text: StyleAndTextTuples = [
        ("class:instructions", DEFAULT_TOOLBAR),
        ("class:message", message),
    ]

    _style: BaseStyle = (
        merge_styles([DEFAULT_STYLE, style])
        if style
        else DEFAULT_STYLE
    )

    return checkboxlist_dialog(
        title=title,
        text=_text,
        values=options if options else [],
        style=_style
).run()