from prettytable import PrettyTable

from .prompts import choice_prompt, confirm_prompt, input_prompt

from ..utils import console_utils as cu
from ..external.sub_sync import Sushi

ADVANCED_SUSHI_ARG_FIELDS = [
    {
        "label": "Window (--window)",
        "attr": "window",
        "type": int,
        "allow_negative": False,
        "default": Sushi.advanced_args_mapping["window"][1],
        "description": "Defines the secondary time window (in seconds) used to search for a matching audio sample in both directions.\nThe algorithm first searches for matches within a 1.5-second window in both directions. If no matches are found, it expands the search to this broader window."
    },
    {
        "label": "Max Window (--max-window)",
        "attr": "max_window",
        "type": int,
        "allow_negative": False,
        "default": Sushi.advanced_args_mapping["max_window"][1],
        "description": "Defines the largest time window (in seconds) used to search for a matching audio sample in both directions.\nIf no matches are found within the secondary window and the rewind threshold is triggered, the algorithm performs a final search using this maximum window as a fallback before giving up on finding a match for a subtitle."
    },
    {
        "label": "Rewind Threshold (--rewind-thresh)",
        "attr": "rewind_thresh",
        "type": int,
        "allow_negative": False,
        "default": Sushi.advanced_args_mapping["rewind_thresh"][1],
        "description": "Determines the number of broken search groups in a row that triggers the algorithm to 'rewind' to the first broken group use the defined max-window as the fallback."
    },
    {
        "label": "Smooth Radius (--smooth-radius)",
        "attr": "smooth_radius",
        "type": int,
        "allow_negative": False,
        "default": Sushi.advanced_args_mapping["smooth_radius"][1],
        "description": "Defines the radius of the running median filter used for smoothing subtitle group timings."
    },
    {
        "label": "Max Typesetting Duration (--max-ts-duration)",
        "attr": "max_ts_duration",
        "type": float,
        "allow_negative": False,
        "default": Sushi.advanced_args_mapping["max_ts_duration"][1],
        "description": "Defines the maximum duration (in seconds) of a line to be considered typesetting."
    },
    {
        "label": "Max Typesetting Distance (--max-ts-distance)",
        "attr": "max_ts_distance",
        "type": float,
        "allow_negative": False,
        "default": Sushi.advanced_args_mapping["max_ts_distance"][1],
        "description": "Defines the maximum distance (in seconds) between two adjacent typesetting lines to be merged."
    }
]

MENU_OPTIONS = [
    (1, "Set Argument Value"),
    (2, "View Arguments Description"),
    (3, "Reset All to Default"),
    (4, "Go Back"),
]


def _format_value(value):
    is_set = value not in (None, "")
    normalized_value = value if is_set else "Default"
    color = cu.Fore.GREEN if is_set else cu.Fore.LIGHTBLACK_EX
    return f"{color}{normalized_value}{cu.style_reset}"


def _render_advanced_sushi_table(settings_obj):
    table = PrettyTable(["Option", "Argument", "Current Value", "Default Value"])
    for idx, field in enumerate(ADVANCED_SUSHI_ARG_FIELDS, 1):
        current_value = settings_obj.sync_workflow.get("sushi_advanced_args", {}).get(field["attr"], None)
        table.add_row([
            idx,
            field["label"],
            _format_value(current_value),
            f"{cu.fore.YELLOW}{field['default']}{cu.style_reset}",
        ])
    return table


def _parse_advanced_input(raw_value, field):
    value_type = field["type"]
    if value_type is str:
        return raw_value.strip() or None

    try: 
        parsed_value = value_type(raw_value)
    except ValueError:
        return None, f"Invalid value. Expected a {value_type.__name__}."

    if not field.get("allow_negative", True) and parsed_value < 0:
        return None, "Value cannot be negative."

    return parsed_value


def _edit_advanced_sushi_arg(settings_obj, field):
    attr = field["attr"]
    current_value = settings_obj.sync_workflow.get("sushi_advanced_args", {}).get(attr, None)
    default_value = field["default"]

   
    print(f"Current value: {_format_value(current_value)}")
    print(f"Sushi default: {_format_value(default_value)}")

    typed_label = field["type"].__name__
    prompt_message = f"Enter {typed_label} value (leave empty for default): "

    while True:
        user_input = input_prompt.get(message=prompt_message, allow_empty=True, nl_before=True)

        if user_input == "":
            if current_value is None:
                cu.print_warning("Already using default value. No changes made.", wait=True)
                return
            settings_obj.sync_workflow["sushi_advanced_args"][attr] = None
            settings_obj._save()
            return

        parsed = _parse_advanced_input(user_input, field)
        if isinstance(parsed, tuple):
            _, error = parsed
            cu.print_error(error, wait=False)
            continue

        if parsed == default_value:
            cu.print_warning("Entered value is the same as the current value. No changes made.", wait=True)
            return

        settings_obj.sync_workflow["sushi_advanced_args"][attr] = parsed
        settings_obj._save()
        return
    
def _select_arg_to_edit():
    options = [(idx, field["label"]) for idx, field in enumerate(ADVANCED_SUSHI_ARG_FIELDS, 1)]
    options.append((len(options) + 1, "Go Back"))

    selected = choice_prompt.get("Select argument to edit: ", options=options)
    if selected == len(options):
        return None

    return ADVANCED_SUSHI_ARG_FIELDS[selected - 1]

def _view_advanced_arg_descriptions():
    cu.print_header("Arguments Description")
    for field in ADVANCED_SUSHI_ARG_FIELDS:
        cu.print_subheader(field['label'])
        print(field["description"] + "\n")
    input_prompt.get("Press Enter to return to the menu... ", allow_empty=True)


def _reset_all_values(settings_obj):
    if confirm_prompt.get("Reset all custom arguments to default values?"):
        for field in settings_obj.sync_workflow.get("sushi_advanced_args", {}).keys():
            settings_obj.sync_workflow["sushi_advanced_args"][field] = None
        settings_obj._save()
        cu.print_success("All advanced arguments have been reset to default values.", wait=True)


def configure_advanced_sushi_args(settings_obj):
    while True:
        cu.clear_screen()
        cu.print_header("Advanced Sushi Arguments\n")
        print(_render_advanced_sushi_table(settings_obj))

        selected = choice_prompt.get(options=MENU_OPTIONS)
        match selected:
            case 1:
                field = _select_arg_to_edit()
                if field:
                    _edit_advanced_sushi_arg(settings_obj, field)
            case 2:
                _view_advanced_arg_descriptions()
            case 3:
                _reset_all_values(settings_obj)
            case 4:
                break

        
