from prompt_toolkit.shortcuts import choice
from prompt_toolkit.styles import Style 

from .. import constants 


DEFAULT_STYLE = Style.from_dict({
    # "frame.border": "#56b6c2",
    "selected-option": f"fg:{constants.COLOR_ACCENT} bold",
    "bottom-toolbar": "#ffffff bg:#333333 noreverse",
})

DEFAULT_TOOLBAR = "Use arrow/number keys or mouse to select an option. Press Enter to confirm."


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
    
def get(message="Select an option: ", options=None, nl_before=True, nl_after=True, show_toolbar=False, **kwargs): 
    """Use prompt_toolkit to display a choice prompt with the given options."""
    normalized_options = options if options is not None else kwargs.get("options")
    _validate_choice_options(normalized_options)

    kwargs["options"] = normalized_options
    kwargs.setdefault("mouse_support", True)
    kwargs.setdefault("style", DEFAULT_STYLE)
    kwargs.setdefault("bottom_toolbar", DEFAULT_TOOLBAR if show_toolbar else None)

    is_frame_enabled = kwargs.get("show_frame", False)

    if nl_before and not message.strip().startswith("\n") and not is_frame_enabled:
        print()

    user_choice = choice(message, **kwargs)

    if nl_after and not message.strip().endswith("\n") and not is_frame_enabled:
        print()
        
    return user_choice