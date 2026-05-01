from enum import StrEnum
from ..models.enums import Task

VIDEO_TASKS: set[Task] = {Task.VIDEO_SYNC_DIR, Task.VIDEO_SYNC_FIL}
AUDIO_TASKS: set[Task] = {Task.AUDIO_SYNC_DIR, Task.AUDIO_SYNC_FIL}

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