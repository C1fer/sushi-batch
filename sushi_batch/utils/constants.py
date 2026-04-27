from ..models.enums import Task

VIDEO_TASKS = (Task.VIDEO_SYNC_DIR, Task.VIDEO_SYNC_FIL)
AUDIO_TASKS = (Task.AUDIO_SYNC_DIR, Task.AUDIO_SYNC_FIL)


COLOR_ACCENT = "#56b6c2"
COLOR_DESTRUCTIVE = "#e06c75"
COLOR_MUTED = "#9aa0a6"
COLOR_MUTED_LIGHTER = "#abb0b6"
COLOR_SUCCESS = "#98c379"
COLOR_TEXT = "#ffffff"
COLOR_BG_DARK = "#1f1f1f"
COLOR_BG_DARKER = "#111111"
COLOR_PENDING = "#f2d574"
COLOR_TOTAL = "#74c7ec"


BOTTOM_TOOLBAR_STATS_SEPARATOR = ("class:bottom-toolbar.sep", " | ")
BOTTOM_TOOLBAR_STATS_STYLES = {
    "bottom-toolbar": f"fg:{COLOR_BG_DARK} bg:{COLOR_MUTED_LIGHTER}",
    "bottom-toolbar.label": f"fg:{COLOR_BG_DARK}",
    "bottom-toolbar.total": f"bg:{COLOR_TOTAL} bold",
    "bottom-toolbar.pending": f"bg:{COLOR_PENDING} bold",
    "bottom-toolbar.completed": f"bg:{COLOR_SUCCESS} bold",
    "bottom-toolbar.failed": f"bg:{COLOR_DESTRUCTIVE} bold",
    "bottom-toolbar.sep": f"bg:{COLOR_MUTED}",
}