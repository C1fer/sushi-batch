from enum import StrEnum
from typing import Callable, Literal

from ..models.enums import AudioChannelLayout, Task

type SelectableOption = tuple[int, str]
type MenuItem = tuple[int, str]
type DynamicMenuItem = tuple[int, str, Callable[[dict[str, bool]], bool]]

type SushiAdvancedArgValue = int | float | None
type SushiAdvancedArgKey = Literal["window", "max_window", "rewind_thresh", "smooth_radius", "max_ts_duration", "max_ts_distance"]

VIDEO_TASKS: set[Task] = {Task.VIDEO_SYNC_DIR, Task.VIDEO_SYNC_FIL}
AUDIO_TASKS: set[Task] = {Task.AUDIO_SYNC_DIR, Task.AUDIO_SYNC_FIL}

# Maps ffprobe channel_layout strings (`ffmpeg -layouts`) to bitrate tiers selected in settings.
FFPROBE_CHANNEL_LAYOUT_MAP: dict[AudioChannelLayout, set[str]] = {
    AudioChannelLayout.MONO: {"mono"},
    AudioChannelLayout.STEREO: {"stereo", "binaural", "downmix"},
    AudioChannelLayout.SURROUND_5_1: {
        "5.0",
        "5.0(side)",
        "5.1",
        "5.1(side)",
        "3.1",
        "3.1.2",
        "quad",
        "quad(side)",
        "hexagonal",
    },
    AudioChannelLayout.SURROUND_7_1: {
        "6.0",
        "6.0(front)",
        "6.1",
        "6.1(back)",
        "6.1(front)",
        "7.0",
        "7.0(front)",
        "7.1",
        "7.1(wide)",
        "7.1(wide-side)",
        "octagonal",
        "cube",
        "7.1.2",
        "7.1.4",
        "7.2.3",
        "9.1.4",
        "9.1.6",
        "hexadecagonal",
        "22.2",
    },
}


class CustomColor(StrEnum):
    ACCENT = "#56b6c2"
    DESTRUCTIVE = "#e06c75"
    MUTED = "#9aa0a6"
    MUTED_LIGHTER = "#abb0b6"
    SUCCESS = "#98c379"
    TEXT = "#ffffff"
    BG_DARK = "#1f1f1f"
    BG_DARKER = "#111111"
    PENDING = "#f2d574"
    TOTAL = "#74c7ec"


BOTTOM_TOOLBAR_STATS_SEPARATOR: tuple[str, str] = ("class:bottom-toolbar.sep", " | ")
BOTTOM_TOOLBAR_STATS_STYLES: dict[str, str] = {
    "bottom-toolbar": f"fg:{CustomColor.BG_DARK} bg:{CustomColor.MUTED_LIGHTER}",
    "bottom-toolbar.label": f"fg:{CustomColor.BG_DARK}",
    "bottom-toolbar.total": f"bg:{CustomColor.TOTAL} bold",
    "bottom-toolbar.pending": f"bg:{CustomColor.PENDING} bold",
    "bottom-toolbar.completed": f"bg:{CustomColor.SUCCESS} bold",
    "bottom-toolbar.failed": f"bg:{CustomColor.DESTRUCTIVE} bold",
    "bottom-toolbar.sep": f"bg:{CustomColor.MUTED}",
}