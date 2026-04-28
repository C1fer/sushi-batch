from copy import deepcopy

from prettytable import PrettyTable

from ..models.enums import AudioEncodeCodec, AudioChannelLayout, AudioEncoder

from .prompts import choice_prompt, confirm_prompt

from ..utils import console_utils as cu
from ..models.settings import DEFAULT_ENCODE_CODEC_SETTINGS

BITRATE_OPTIONS = {
   AudioEncodeCodec.OPUS: {
        AudioChannelLayout.MONO: [
            ("64k (Recommended)", "64k"),
            ("48k (Efficient)", "48k"),
            ("32k (Minimum recommended)", "32k"),
        ],
        AudioChannelLayout.STEREO: [
            ("192k (Placebo)", "192k"),
            ("160k (Covers edge cases)", "160k"),
            ("128k (Recommended)", "128k"),
            ("96k (Efficient)", "96k"),
        ],
        AudioChannelLayout.SURROUND_5_1: [
            ("384k (Placebo)", "384k"),
            ("320k (Recommended)", "320k"),
            ("256k (Efficient)", "256k"),
            ("192k (Minimum recommended)", "192k"),
        ],
        AudioChannelLayout.SURROUND_7_1: [
            ("510k (Placebo)", "510k"), # Capped at Opus spec limit
            ("448k (Recommended)", "448k"),
            ("384k (Efficient)", "384k"),
        ],
    },

    AudioEncodeCodec.AAC: {
        AudioChannelLayout.MONO: [
            ("96k (Placebo)", "96k"),
            ("64k (Recommended)", "64k"),
            ("48k (Efficient / Voice)", "48k"),
        ],
        AudioChannelLayout.STEREO: [
            ("256k (Placebo)", "256k"),
            ("192k (Recommended)", "192k"),
            ("128k (Efficient)", "128k"),
        ],
        AudioChannelLayout.SURROUND_5_1: [
            ("512k (Placebo)", "512k"),
            ("448k (Recommended)", "448k"),
            ("384k (Efficient)", "384k"),
        ],
        AudioChannelLayout.SURROUND_7_1: [
            ("768k (Placebo)", "768k"),
            ("640k (Recommended)", "640k"),
            ("576k (Efficient)", "576k"),
        ], 
    },

   AudioEncodeCodec.EAC3: {
        AudioChannelLayout.MONO: [
            ("128k (Placebo)", "128k"),
            ("96k (Recommended)", "96k"),
            ("64k (Efficient)", "64k"),
        ],
        AudioChannelLayout.STEREO: [
            ("256k (Placebo)", "256k"),
            ("224k (Recommended)", "224k"), # 224k is a sweet spot for EAC3 Stereo
            ("160k (Efficient)", "160k"),
        ],
        AudioChannelLayout.SURROUND_5_1: [
            ("640k (Placebo)", "640k"),
            ("448k (Recommended)", "448k"),
            ("384k (Efficient)", "384k"),
        ],
        AudioChannelLayout.SURROUND_7_1: [
            ("1024k (Placebo)", "1024k"), 
            ("768k (Recommended)", "768k"),
            ("640k (Efficient)", "640k"),
        ],
    },
}

ENCODER_OPTIONS = {
    AudioEncodeCodec.OPUS: [
        ("libopus (FFmpeg)", AudioEncoder.FFMPEG),
        ("opusenc (opus-tools)", AudioEncoder.XIPH_OPUSENC),
    ],
    AudioEncodeCodec.AAC: [], # Encoder choice not exposed for now
    AudioEncodeCodec.EAC3: [], # Encoder choice not exposed for now
}

MENU_OPTIONS = [
    (1, "Change Setting Value"),
    (2, "Reset All to Default"),
    (3, "Go Back"),
]

def _get_base_options_rows(codec):
    return [
        {
            "label": "Mono Bitrate",
            "attr": f"bitrates.{AudioChannelLayout.MONO.name}",
            "type": str,
            "default": DEFAULT_ENCODE_CODEC_SETTINGS[codec.name]["bitrates"]["MONO"],
            "prompt": "Select new bitrate for Mono layout: ",
        },
        {
            "label": "Stereo Bitrate",
            "attr": f"bitrates.{AudioChannelLayout.STEREO.name}",
            "type": str,
            "default": DEFAULT_ENCODE_CODEC_SETTINGS[codec.name]["bitrates"]["STEREO"],
            "prompt": "Select new bitrate for Stereo layout: ",
        },
        {   
            "label": "5.1 Bitrate",
            "attr": f"bitrates.{AudioChannelLayout.SURROUND_5_1.name}",
            "type": str,
            "default": DEFAULT_ENCODE_CODEC_SETTINGS[codec.name]["bitrates"]["SURROUND_5_1"],
            "prompt": "Select new bitrate for 5.1 layout: ",
        },
        {
            "label": "7.1 Bitrate",
            "attr": f"bitrates.{AudioChannelLayout.SURROUND_7_1.name}",
            "type": str,
            "default": DEFAULT_ENCODE_CODEC_SETTINGS[codec.name]["bitrates"]["SURROUND_7_1"],
            "prompt": "Select new bitrate for 7.1 layout: ",
        },
    ]

def _get_visible_options_rows(codec):
    options = _get_base_options_rows(codec)
    if codec == AudioEncodeCodec.OPUS:
        options.insert(0, {
            "label": "Encoder",
            "attr": "encoder",
            "type": AudioEncoder,
            "default": DEFAULT_ENCODE_CODEC_SETTINGS[codec.name]["encoder"],
            "prompt": "Select audio encoder: ",
        })
    return options

def _get_normalized_value(value):
    match value:
        case AudioEncoder():
            return value.value
        case _:
            return value

def _format_value(value, is_default):
    normalized_value = _get_normalized_value(value) if not is_default else "Default"
    color = cu.Fore.GREEN if not is_default else cu.Fore.LIGHTBLACK_EX
    return f"{color}{normalized_value}{cu.style_reset}"

def _get_current_value(settings_obj, codec, attr):
    base_settings = settings_obj.merge_workflow["encode_codec_settings"][codec.name]

    attr_parts = attr.split(".")
    if len(attr_parts) == 1:
        return base_settings.get(attr, None)
    elif len(attr_parts) == 2:
        return base_settings.get(attr_parts[0], {}).get(attr_parts[1], None)
    
def _generate_settings_table(settings_obj, visible_rows, codec):
    table = PrettyTable(["Option", "Current Value", "Default Value"])
    for field in visible_rows:
        current_value = _get_current_value(settings_obj, codec, field["attr"])
        is_default = current_value == field["default"]

        table.add_row([
            field["label"],
            _format_value(_get_normalized_value(current_value), is_default),
            f"{cu.fore.YELLOW}{_get_normalized_value(field['default'])}{cu.style_reset}",
        ])
    return table

def _update_selection(settings_obj, field, codec, options):
    current_value = _get_current_value(settings_obj, codec, field["attr"])

    _options = []
    default_option = None
    for idx, (display, value) in enumerate(options, 1):
        if idx == len(options): # Last option, add Go Back
            _options.extend([
                (idx, display),
                (idx+1, "Go Back"),
            ]) 
        else:
            _options.append((idx, display))
        
        if value == current_value:
            default_option = idx
            
    _prompt = field["prompt"] or "Select an option:"
    selected = choice_prompt.get(_prompt, options=_options, default=default_option)
    if selected == len(_options):
        return
    
    new_value = options[selected - 1][1]

    if new_value != current_value:
        base_key = settings_obj.merge_workflow["encode_codec_settings"][codec.name]
        
        parts = field["attr"].split(".")
        if len(parts) == 1:
            base_key[field["attr"]] = new_value
        elif len(parts) == 2:
            base_key[parts[0]][parts[1]] = new_value

        settings_obj._save()
    
def _edit_codec_setting(settings_obj, field, codec):
    if field["type"] == AudioEncoder:
        _update_selection(settings_obj, field, codec, ENCODER_OPTIONS[codec])
    elif "bitrates." in field["attr"]:
        layout_name = field["attr"].split(".")[1]
        options = BITRATE_OPTIONS[codec][AudioChannelLayout[layout_name]]
        _update_selection(settings_obj, field, codec, options)

def _select_setting_to_update(visible_rows):
    options = [(idx, row["label"]) for idx, row in enumerate(visible_rows, 1)]
    options.append((len(options) + 1, "Go Back"))

    selected = choice_prompt.get("Select option to edit: ", options=options)
    if selected == len(options):
        return None

    return visible_rows[selected - 1]

def _reset_all_values(settings_obj, selected_codec):
    if confirm_prompt.get("Reset all custom arguments to default values?"):
        settings_obj.merge_workflow["encode_codec_settings"][selected_codec.name] = (
            deepcopy(DEFAULT_ENCODE_CODEC_SETTINGS[selected_codec.name])
        )
        settings_obj._save()
        cu.print_success("All settings have been reset to default.", wait=True)


def configure_audio_encode_settings(settings_obj, selected_codec):
    while True:
        cu.clear_screen()
        cu.print_header(f"{selected_codec.value} Encode Settings \n")

        visible_rows = _get_visible_options_rows(selected_codec)
        print(_generate_settings_table(settings_obj, visible_rows, selected_codec))

        selected = choice_prompt.get(options=MENU_OPTIONS)
        match selected:
            case 1:
                field = _select_setting_to_update(visible_rows)
                if field:
                    _edit_codec_setting(settings_obj, field, selected_codec)
            case 2:
                _reset_all_values(settings_obj, selected_codec)
            case 3:
                break

        
