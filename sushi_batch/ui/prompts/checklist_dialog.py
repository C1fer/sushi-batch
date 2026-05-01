from prompt_toolkit.shortcuts import checkboxlist_dialog
from prompt_toolkit.styles import Style

from ...utils.constants import CustomColor

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

def get(title="", message="Select options: ", options=None):
    _text = [
        ("class:instructions", DEFAULT_TOOLBAR),
        ("class:message", message),
    ]

    return checkboxlist_dialog(
        title=title,
        text=_text,
        values=_validate_choice_options(options),
        style=DEFAULT_STYLE
).run()