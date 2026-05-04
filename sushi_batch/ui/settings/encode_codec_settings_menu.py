from copy import deepcopy
from typing import TypedDict, cast

from prettytable import PrettyTable

from ...external.opusenc import XiphOpusEncoder
from ...models.enums import AudioChannelLayout, AudioEncodeCodec, AudioEncoder
from ...models.settings import (
    DEFAULT_ENCODE_CODEC_SETTINGS,
    AACEncodeProfile,
    EAC3EncodeProfile,
    OpusEncodeProfile,
    Settings,
)
from ...utils import console_utils as cu
from ...utils.constants import MenuItem, SelectableOption
from ..prompts import choice_prompt, confirm_prompt, input_prompt

type CodecOptionValue = str | AudioEncoder
class CodecSettingsRow(TypedDict):
    label: str
    attr: str
    type: type
    default: CodecOptionValue
    prompt: str
    description: str | tuple[str, ...]
    show: bool

BITRATE_OPTIONS: dict[AudioEncodeCodec, dict[AudioChannelLayout, list[tuple[str, str]]]] = {
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

ENCODER_OPTIONS: dict[AudioEncodeCodec, list[tuple[str, AudioEncoder]]] = {
    AudioEncodeCodec.OPUS: [
        ("libopus (FFmpeg)", AudioEncoder.LIBOPUS_FFMPEG),
        ("opusenc (opus-tools)", AudioEncoder.XIPH_OPUSENC),
    ],
    AudioEncodeCodec.AAC: [
        ("aac (FFmpeg)", AudioEncoder.AAC_FFMPEG),
    ], # Encoder choice not exposed for now
    AudioEncodeCodec.EAC3: [
        ("eac3 (FFmpeg)", AudioEncoder.EAC3_FFMPEG),
    ], # Encoder choice not exposed for now
}

MENU_OPTIONS: list[MenuItem] = [
    (1, "Change Setting Value"),
    (2, "Reset All to Default"),
    (3, "View Options Help"),
    (4, "Go Back"),
]

def _get_base_options_rows(codec: AudioEncodeCodec) -> list[CodecSettingsRow]:
    return [
        {
            "label": "Encoder",
            "attr": "encoder",
            "type": AudioEncoder,
            "default": DEFAULT_ENCODE_CODEC_SETTINGS[codec.name]["encoder"],
            "prompt": "Select audio encoder: ",
            "description": "",
            "show": codec == AudioEncodeCodec.OPUS,
        },
        {
            "label": "Mono Bitrate",
            "attr": f"bitrates.{AudioChannelLayout.MONO.name}",
            "type": str,
            "default": DEFAULT_ENCODE_CODEC_SETTINGS[codec.name]["bitrates"][AudioChannelLayout.MONO.name],
            "prompt": "Select new bitrate for Mono layout: ",
            "description": "Target bitrate for Mono audio tracks.",
            "show": True,
        },
        {
            "label": "Stereo Bitrate",
            "attr": f"bitrates.{AudioChannelLayout.STEREO.name}",
            "type": str,
            "default": DEFAULT_ENCODE_CODEC_SETTINGS[codec.name]["bitrates"]["STEREO"],
            "prompt": "Select new bitrate for Stereo layout: ",
            "description": "Target bitrate for Stereo audio tracks.",
            "show": True,
        },
        {   
            "label": "5.1 Bitrate",
            "attr": f"bitrates.{AudioChannelLayout.SURROUND_5_1.name}",
            "type": str,
            "default": DEFAULT_ENCODE_CODEC_SETTINGS[codec.name]["bitrates"]["SURROUND_5_1"],
            "prompt": "Select new bitrate for 5.1 layout: ",
            "description": "Target bitrate for 5.1 audio tracks",
            "show": True,
        },
        {
            "label": "7.1 Bitrate",
            "attr": f"bitrates.{AudioChannelLayout.SURROUND_7_1.name}",
            "type": str,
            "default": DEFAULT_ENCODE_CODEC_SETTINGS[codec.name]["bitrates"]["SURROUND_7_1"],
            "prompt": "Select new bitrate for 7.1 layout: ",
            "description": "Target bitrate for 7.1 audio tracks",
            "show": True,
        },
    ]

def _get_visible_options_rows(codec: AudioEncodeCodec) -> list[CodecSettingsRow]:
    visible_rows: list[CodecSettingsRow] = []
    for row in _get_base_options_rows(codec):
        if row["type"] == AudioEncoder and codec == AudioEncodeCodec.OPUS:
            row["description"] = (
                "Audio encoder to be used for Opus encoding.", 
                f"{cu.fore.LIGHTWHITE_EX} - libopus.{cu.style_reset} Default encoder provided by FFmpeg. Suitable for most users.{cu.style_reset}", 
                f"{cu.fore.LIGHTWHITE_EX} - opusenc.{cu.style_reset} Official Opus encoder. Recommended for users who want to ensure maximum compatibility with the Opus specification.",
                f"{cu.fore.LIGHTBLACK_EX}   - Requires opus-tools to be installed and added to PATH.{cu.style_reset}"
            )
        if row["show"]:
            visible_rows.append(row)
    return visible_rows

def _get_normalized_value(value: CodecOptionValue | None) -> str:
    match value:
        case AudioEncoder():
            return value.value
        case _:
            return value or "N/A"

def _format_value(value: CodecOptionValue, is_default: bool) -> str:
    normalized_value = _get_normalized_value(value) if not is_default else "Default"
    color = cu.Fore.GREEN if not is_default else cu.Fore.LIGHTBLACK_EX
    return f"{color}{normalized_value}{cu.style_reset}"

def _get_current_value(settings_obj: Settings, codec: AudioEncodeCodec, attr: str) -> CodecOptionValue | None:
    base_settings: AACEncodeProfile | EAC3EncodeProfile | OpusEncodeProfile = settings_obj.merge_workflow["encode_codec_settings"][codec.name]
    
    attr_parts: list[str] = attr.split(".")
    if len(attr_parts) == 1:
        return base_settings.get(attr)
    elif len(attr_parts) == 2:
        return base_settings.get(attr_parts[0], {}).get(attr_parts[1], None)
    
def _generate_settings_table(settings_obj: Settings, visible_rows: list[CodecSettingsRow], codec: AudioEncodeCodec) -> PrettyTable:
    table = PrettyTable(["Option", "Current Value", "Default Value"])
    for field in visible_rows:
        current_value: CodecOptionValue | None = _get_current_value(settings_obj, codec, field["attr"])
        is_default: bool = current_value == field["default"]

        table.add_row([
            field["label"],
            _format_value(_get_normalized_value(current_value), is_default),
            f"{cu.fore.YELLOW}{_get_normalized_value(field['default'])}{cu.style_reset}",
        ])
    return table

def _update_selection(settings_obj: Settings, field: CodecSettingsRow, codec: AudioEncodeCodec, options: list[tuple[str, str]] | list[tuple[str, AudioEncoder]], warning_bottom_bar: str | None = None) -> None:
    current_value: CodecOptionValue | None = _get_current_value(settings_obj, codec, field["attr"])
    _prompt: str = field["prompt"] or "Select an option:"
    _options: list[SelectableOption] = []
    default_option: int = 0

    for idx, (display, value) in enumerate[tuple[str, AudioEncoder] | tuple[str, str]](options, 1):
        if idx == len(options): # Last option, add Go Back
            _options.extend([
                (idx, display),
                (idx+1, "Go Back"),
            ]) 
        else:
            _options.append((idx, display))
        
        if value == current_value:
            default_option = idx
            
    selected: int = choice_prompt.get(_prompt, options=_options, default_option=default_option, bottom_toolbar=warning_bottom_bar)
    if selected == len(_options):
        return
    
    new_value: CodecOptionValue = options[selected - 1][1]

    if new_value != current_value:
        base_key: AACEncodeProfile | EAC3EncodeProfile | OpusEncodeProfile = settings_obj.merge_workflow["encode_codec_settings"][codec.name]
        
        parts: list[str] = field["attr"].split(".")
        if len(parts) == 1 and parts[0] == "encoder":
            base_key["encoder"] = cast(AudioEncoder, new_value)
        elif len(parts) == 2 and parts[0] == "bitrates":
            base_key["bitrates"][parts[1]] = cast(str, new_value)
        else:
            raise ValueError(f"Unknown encode codec setting attr: {field['attr']!r}")

        settings_obj.handle_save()
    
def _edit_codec_setting(settings_obj: Settings, field: CodecSettingsRow, codec: AudioEncodeCodec, warning_bottom_bar: str | None = None) -> None:
    if field["type"] == AudioEncoder:
        _update_selection(settings_obj, field, codec, ENCODER_OPTIONS[codec], warning_bottom_bar)
    elif "bitrates." in field["attr"]:
        layout_name: str = field["attr"].split(".")[1]
        options: list[tuple[str, str]] = BITRATE_OPTIONS[codec][AudioChannelLayout[layout_name]]
        _update_selection(settings_obj, field, codec, options)

def _select_setting_to_update(visible_rows: list[CodecSettingsRow], warning_bottom_bar: str | None = None) -> CodecSettingsRow | None:
    options: list[SelectableOption] = [(idx, row["label"]) for idx, row in enumerate(visible_rows, 1)]
    options.append((len(options) + 1, "Go Back"))

    selected: int = choice_prompt.get("Select option to edit: ", options=options, bottom_toolbar=warning_bottom_bar)
    if selected == len(options):
        return None

    return visible_rows[selected - 1]

def _reset_all_values(settings_obj: Settings, selected_codec: AudioEncodeCodec) -> None:
    if confirm_prompt.get("Reset all settings for this codec?",destructive=True):
        settings_obj.merge_workflow["encode_codec_settings"][selected_codec.name] = (
            deepcopy(DEFAULT_ENCODE_CODEC_SETTINGS[selected_codec.name])
        )
        settings_obj.handle_save()
        cu.print_success("All settings for this codec have been reset to default.", wait=True)

def _view_options_help(visible_rows: list[CodecSettingsRow]) -> None:
    cu.print_header("Help")
    for field in visible_rows:
        cu.print_help_text(field["label"], field["description"])
    print()
    input_prompt.get("Press Enter to close...  ", allow_empty=True, nl_before=True)

def _get_warning_bottom_bar(selected_codec: AudioEncodeCodec, settings_obj: Settings) -> str | None:
    if selected_codec == AudioEncodeCodec.OPUS:
        selected_encoder: AudioEncoder = settings_obj.merge_workflow["encode_codec_settings"][selected_codec.name]["encoder"]
        if not XiphOpusEncoder.is_available and selected_encoder == AudioEncoder.XIPH_OPUSENC:
            return " Opusenc is not installed. FFmpeg will be used instead.\n Updated builds can be found at https://www.videohelp.com/software/OpusTools "
        return None

def configure_audio_encode_settings(settings_obj: Settings, selected_codec: AudioEncodeCodec) -> None:
    while True:
        cu.clear_screen()
        cu.print_header(f"{selected_codec.value} Encode Settings \n")

        visible_rows: list[CodecSettingsRow] = _get_visible_options_rows(selected_codec)
        print(_generate_settings_table(settings_obj, visible_rows, selected_codec))

        warning_bottom_bar: str | None = _get_warning_bottom_bar(selected_codec, settings_obj)

        selected: int = choice_prompt.get(options=MENU_OPTIONS, bottom_toolbar=warning_bottom_bar)
        match selected:
            case 1:
                field: CodecSettingsRow | None = _select_setting_to_update(visible_rows, warning_bottom_bar)
                if field:
                    _edit_codec_setting(settings_obj, field, selected_codec, warning_bottom_bar)
            case 2:
                _reset_all_values(settings_obj, selected_codec)
            case 3:
                _view_options_help(visible_rows)
            case _:
                break

        
