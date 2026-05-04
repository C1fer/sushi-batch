import re

from art import text2art

from ..external.mkv_merge import MKVMerge
from ..external.sub_resample import SubResampler
from ..models.settings import Settings
from ..utils import console_utils as cu
from ..utils.constants import MenuItem
from .queue.queue_manager import main_queue, get_queue_stats_by_key
from .queue.main_queue import show_main_queue
from .help_menu import show_help_screen
from .job_create_menu import show_job_create_menu
from .prompts import choice_prompt
from ..ui.settings.settings_menu import show_settings_menu

DEFAULT_TOOLBAR = " Use arrow/number keys or mouse to select an option. Press Enter to confirm."

MENU_OPTIONS: list[MenuItem] = [
    (1, "Create Video Sync Job"),
    (2, "Create Audio Sync Job"),
    (3, "View Job Queue"),
    (4, "Settings"),
    (5, "Help"),
    (6, "Exit")
]


def _get_status_box(version: str) -> str:
    """Get the status box for the main menu."""
    pending_jobs_count: int = get_queue_stats_by_key(queue=main_queue.contents, key="pending")
    _count_display: str = "None" if not pending_jobs_count else str(pending_jobs_count)
    pending_jobs_display = f"{cu.fore.LIGHTBLACK_EX}Pending Jobs: {cu.fore.LIGHTYELLOW_EX}{_count_display}{cu.fore.RESET}"

    version_display: str = f"{cu.fore.LIGHTBLACK_EX}Version: {cu.fore.YELLOW}{version}"
    mkvmerge_status_display: str = cu.get_formatted_install_status("MKVMerge", MKVMerge.is_installed, not_found_label="Not Found (Merging Disabled)")
    sub_resampler_status_display: str = cu.get_formatted_install_status("Aegisub-CLI", SubResampler.is_installed, not_found_label="Not Found (Subtitle Resampling Disabled)")
    status_bar = f"{version_display}   {pending_jobs_display}   {mkvmerge_status_display}   {sub_resampler_status_display}"
    
    visible_status: str = re.sub(r"\x1b\[[0-9;]*m", "", status_bar)
    box_width = len(visible_status) + 4
    box_display =  f"{cu.fore.RESET}+{'-' * (box_width - 2)}+"
    status_box: str = "\n".join([box_display, f"| {status_bar} |", box_display])

    return status_box

def _handle_main_menu_selection(selected_option: int, settings_obj: Settings) -> bool:
    if selected_option not in (3, 6):
        cu.clear_screen()

    match selected_option:
        case 1:
            show_job_create_menu(is_video=True)
        case 2:
            show_job_create_menu(is_video=False)
        case 3:
            if main_queue.contents:
                show_main_queue()
            else:
                cu.print_error("No jobs queued!")
        case 4:
            show_settings_menu(settings_obj)
        case 5:
            show_help_screen()
        case 6:
            return True

    return False

def run_main_menu(version: str, settings_obj: Settings) -> None:
    """Display the main menu and handle user interactions."""
    header: str = text2art("\nSushi Batch")
    while True:
        cu.clear_screen()
        cu.print_header(header + _get_status_box(version))
        selected_option: int = choice_prompt.get(
            message="Select an option: ", 
            options=MENU_OPTIONS, 
            bottom_toolbar=DEFAULT_TOOLBAR,
            nl_before=True,
            show_frame=True
        )

        exit_loop: bool = _handle_main_menu_selection(selected_option, settings_obj)
        if exit_loop:
            break
