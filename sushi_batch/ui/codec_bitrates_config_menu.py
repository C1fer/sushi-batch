from prettytable import PrettyTable

from ..models.enums import AudioEncodeCodec, AudioChannelLayout

from .prompts import choice_prompt, confirm_prompt

from ..utils import console_utils as cu
from ..models.settings import DEFAULT_ENCODE_AUDIO_BITRATES


CODEC_OPTIONS = {
    AudioEncodeCodec.OPUS: {
        AudioChannelLayout.STEREO: [
            ("160k (High-quality stereo music)", "160k"),
            ("128k (Balanced stereo)", "128k"),
            ("96k (Efficient stereo)", "96k"),
            ("64k (Low bitrate / voice)", "64k"),
        ],
        AudioChannelLayout.SURROUND_5_1: [
            ("384k (Very high-quality 5.1 surround)", "384k"),
            ("320k (High-quality 5.1 surround)", "320k"),
            ("256k (Good 5.1 surround)", "256k"),
        ],
        AudioChannelLayout.SURROUND_7_1: [
            ("512k (High-quality 7.1 surround)", "512k"),
            ("448k (Balanced 7.1 surround)", "448k"),
            ("384k (Minimum recommended 7.1)", "384k"),
        ],
    },

    AudioEncodeCodec.AAC: {
        AudioChannelLayout.STEREO: [
            ("256k (High-quality stereo / near-transparent)", "256k"),
            ("192k (Recommended stereo)", "192k"),
            ("128k (Balanced stereo)", "128k"),
            ("96k (Low bitrate stereo / voice)", "96k"),
        ],
        AudioChannelLayout.SURROUND_5_1: [
            ("512k (High-quality 5.1 surround)", "512k"),
            ("448k (Balanced 5.1 surround)", "448k"),
            ("384k (Minimum recommended 5.1)", "384k"),
        ],
        AudioChannelLayout.SURROUND_7_1: [
            ("768k (High-quality 7.1 surround)", "768k"),
            ("640k (Balanced 7.1 surround)", "640k"),
            ("576k (Minimum recommended 7.1)", "576k"),
        ],
    },

    AudioEncodeCodec.EAC3: {
        AudioChannelLayout.STEREO: [
            ("256k (High-quality stereo)", "256k"),
            ("192k (Standard stereo)", "192k"),
            ("128k (Low bitrate stereo / voice)", "128k"),
        ],
        AudioChannelLayout.SURROUND_5_1: [
            ("640k (Recommended 5.1 surround)", "640k"),
            ("512k (High-quality 5.1)", "512k"),
            ("384k (Efficient 5.1 streaming)", "384k"),
        ],
        AudioChannelLayout.SURROUND_7_1: [
            ("768k (High-quality 7.1 surround)", "768k"),
            ("640k (Balanced 7.1 surround)", "640k"),
        ],
    },
}

MENU_OPTIONS = [
    (1, "Change Bitrate Values"),
    (2, "Reset All to Default"),
    (3, "Go Back"),
]


def _format_value(value, is_default):
    normalized_value = value if not is_default else "Default"
    color = cu.Fore.GREEN if not is_default else cu.Fore.LIGHTBLACK_EX
    return f"{color}{normalized_value}{cu.style_reset}"


def _render_bitrates_table(settings_obj):
    table = PrettyTable(["Layout", "Current Value", "Default Value"])
    codec = settings_obj.encode_ffmpeg_codec
    layout_options = CODEC_OPTIONS.get(codec, {})
    for layout, _ in layout_options.items():
        current_value = settings_obj.encode_audio_bitrates.get(codec.name, {}).get(layout.name)
        default_value = DEFAULT_ENCODE_AUDIO_BITRATES.get(codec.name, {}).get(layout.name, "Default")
        table.add_row([
            layout.value,
            _format_value(current_value, current_value == default_value),
            f"{cu.fore.YELLOW}{default_value}{cu.style_reset}",
        ])
    return table

def _update_layout_bitrate(settings_obj, layout):
    codec = settings_obj.encode_ffmpeg_codec
    current_bitrate = settings_obj.encode_audio_bitrates.get(codec.name, {}).get(layout.name)

    options = CODEC_OPTIONS.get(codec, {}).get(layout, [])
    _choice_options = [(idx, desc) for idx, (desc, _) in enumerate(options, 1)]
    _choice_options.append((len(options) + 1, "Go Back"))
    
    selected = choice_prompt.get(f"Select new bitrate for {layout.value}: ", options=_choice_options)
    if selected == len(options):
        return
    
    new_bitrate = options[selected - 1][1]

    if new_bitrate != current_bitrate:
        settings_obj.encode_audio_bitrates[codec.name][layout.name] = new_bitrate
        settings_obj._save()
    
def _select_layout_to_edit():
    options = [(idx, layout.value) for idx, layout in enumerate(AudioChannelLayout, 1)]
    options.append((len(options) + 1, "Go Back"))

    selected = choice_prompt.get("Select argument to edit: ", options=options)
    if selected == len(options):
        return None

    return next(layout for idx, layout in enumerate(AudioChannelLayout, 1) if idx == selected)


def _reset_all_values(settings_obj):
    if confirm_prompt.get("Reset all custom arguments to default values?"):
        setattr(settings_obj, "encode_audio_bitrates", DEFAULT_ENCODE_AUDIO_BITRATES.copy())
        settings_obj._save()
        cu.print_success("All bitrate values have been reset to default.", wait=True)


def configure_audio_encode_bitrates(settings_obj):
    while True:
        cu.clear_screen()
        cu.print_header(f"{settings_obj.encode_ffmpeg_codec.value} Encode Bitrates \n")
        print(_render_bitrates_table(settings_obj))

        selected = choice_prompt.get(options=MENU_OPTIONS)
        match selected:
            case 1:
                channel_layout = _select_layout_to_edit()
                if channel_layout:
                    _update_layout_bitrate(settings_obj, channel_layout)
            case 2:
                _reset_all_values(settings_obj)
            case 3:
                break

        
