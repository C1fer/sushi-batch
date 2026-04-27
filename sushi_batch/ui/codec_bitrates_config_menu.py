from prettytable import PrettyTable

from ..models.enums import AudioEncodeCodec, AudioChannelLayout

from .prompts import choice_prompt, confirm_prompt

from ..utils import console_utils as cu
from ..models.settings import DEFAULT_ENCODE_AUDIO_BITRATES


CODEC_OPTIONS = {
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
    codec = settings_obj.merge_workflow.get("encode_ffmpeg_codec")
    layout_options = CODEC_OPTIONS.get(codec, {})
    for layout, _ in layout_options.items():
        current_value = settings_obj.merge_workflow.get("encode_audio_bitrates", {}).get(codec.name, {}).get(layout.name)
        default_value = DEFAULT_ENCODE_AUDIO_BITRATES.get(codec.name, {}).get(layout.name, "Default")
        table.add_row([
            layout.value,
            _format_value(current_value, current_value == default_value),
            f"{cu.fore.YELLOW}{default_value}{cu.style_reset}",
        ])
    return table

def _update_layout_bitrate(settings_obj, layout):
    codec = settings_obj.merge_workflow.get("encode_ffmpeg_codec")
    current_bitrate = settings_obj.merge_workflow.get("encode_audio_bitrates", {}).get(codec.name, {}).get(layout.name)

    options = CODEC_OPTIONS.get(codec, {}).get(layout, [])
    _choice_options = [(idx, desc) for idx, (desc, _) in enumerate(options, 1)]
    _choice_options.append((len(options) + 1, "Go Back"))
    
    selected = choice_prompt.get(f"Select new bitrate for {layout.value}: ", options=_choice_options)
    if selected == len(_choice_options):
        return
    
    new_bitrate = options[selected - 1][1]

    if new_bitrate != current_bitrate:
        settings_obj.merge_workflow["encode_audio_bitrates"][codec.name][layout.name] = new_bitrate
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
        settings_obj.merge_workflow["encode_audio_bitrates"] = DEFAULT_ENCODE_AUDIO_BITRATES.copy()
        settings_obj._save()
        cu.print_success("All bitrate values have been reset to default.", wait=True)


def configure_audio_encode_bitrates(settings_obj):
    while True:
        cu.clear_screen()
        cu.print_header(f"{settings_obj.merge_workflow.get('encode_ffmpeg_codec').value} Encode Bitrates \n")
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

        
