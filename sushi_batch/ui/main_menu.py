import re

from art import text2art

from ..external.mkv_merge import MKVMerge
from ..external.sub_resample import SubResampler

from ..models.enums import Task
from ..models.job_queue import JobQueue
from ..utils import console_utils as cu
from ..utils import file_utils
from . import queue_manager as qm
from .prompts import choice_prompt

from .settings_menu import show_settings_menu

DEFAULT_TOOLBAR = " Use arrow/number keys or mouse to select an option. Press Enter to confirm."

VIDEO_SYNC_INFO = """Selected tracks are extracted from reference and target videos. Subtitle is adjusted to sync with the target audio.
The generated subtitle can later be merged with the target video in the Job Queue."""

AUDIO_SYNC_INFO = "Provided audio tracks are analyzed to determine timing differences. Subtitle is adjusted to sync with the target audio." 

SYNC_MODES_INFO = """
Directory Mode: Choose source and target folders; matching files are paired automatically by filename.
File-select Mode: Choose source and target files manually."""

MENU_OPTIONS = {
    "top": [
        (1, "Create Video Sync Job"),
        (2, "Create Audio Sync Job"),
        (3, "View Job Queue"),
        (4, "Settings"),
        (5, "Exit")
    ],
    "sub_video_sync": {
        "title": "Create Video Sync Job",
        "values": [
            (1, "Directory Mode"),
            (2, "File-select Mode"),
            (3, "Go Back")
        ],
        
    },
    "sub_audio_sync": {
        "title": "Create Audio Sync Job",
        "values": [
            (1, "Directory Mode"),
            (2, "File-select Mode"),
            (3, "Go Back")
        ],
    }
}


def handle_sync_option_selection(task):
    jobs = None

    if task in (Task.AUDIO_SYNC_DIR, Task.VIDEO_SYNC_DIR):
        src, dst = file_utils.get_directories()
        if src and dst:
            jobs = file_utils.search_directories(src, dst, task)
    else:
        jobs = file_utils.select_files(task)

    if jobs:
        return qm.show_temp_queue(JobQueue(jobs), task)

    return False

def _show_sync_submenu(is_video_sync=True):
    submenu_key = "sub_video_sync" if is_video_sync else "sub_audio_sync"
    task_options = {
        1: Task.VIDEO_SYNC_DIR if is_video_sync else Task.AUDIO_SYNC_DIR,
        2: Task.VIDEO_SYNC_FIL if is_video_sync else Task.AUDIO_SYNC_FIL
    }

    while True:
        cu.clear_screen()
        cu.print_header(MENU_OPTIONS[submenu_key]["title"])
        cu.print_subheader(VIDEO_SYNC_INFO if is_video_sync else AUDIO_SYNC_INFO)
        print(f"{cu.fore.LIGHTBLACK_EX}{SYNC_MODES_INFO}")

        selected_sub_option = choice_prompt.get(
            "Select an option: ",
            MENU_OPTIONS[submenu_key]["values"],
            show_frame=True,
            nl_before=True,
        )

        if selected_sub_option == 3:
            return

        task = task_options.get(selected_sub_option)
        if task is None:
            cu.print_error("Invalid choice! Please select a valid option.", False)
            continue

        should_return_to_main_menu = handle_sync_option_selection(task)
        if should_return_to_main_menu:
            return


def _handle_main_menu_selection(selected_option, settings_obj):
    if selected_option != 5:
        cu.clear_screen()

    match selected_option:
        case 1:
            _show_sync_submenu(is_video_sync=True)
        case 2:
            _show_sync_submenu(is_video_sync=False)
        case 3:
            if qm.main_queue.contents:
                qm.show_main_queue(Task.JOB_QUEUE)
            else:
                cu.print_error("No jobs queued!")
        case 4:
            show_settings_menu(settings_obj)
        case 5:
            return False

    return True


def _get_menu_info(version):
    header = text2art("\nSushi Batch")

    version_info = f"{cu.fore.LIGHTBLACK_EX}Version: {cu.fore.YELLOW}{version}"
    mkvmerge_status = cu.get_formatted_install_status("MKVMerge", MKVMerge.is_installed, not_found_label="Not Found (Merging Disabled)")
    sub_resampler_status = cu.get_formatted_install_status("Aegisub-CLI", SubResampler.is_installed, not_found_label="Not Found (Subtitle Resampling Disabled)")
    pending_job_count = f"{cu.fore.LIGHTBLACK_EX}Pending Jobs: {cu.fore.LIGHTYELLOW_EX}{qm.get_queue_stats()['pending']}{cu.fore.RESET}"
    status_bar = f"{version_info}   {pending_job_count}   {mkvmerge_status}   {sub_resampler_status}"
    
    visible_status = re.sub(r"\x1b\[[0-9;]*m", "", status_bar)
    box_width = len(visible_status) + 4
    box_display =  f"{cu.fore.RESET}+{'-' * (box_width - 2)}+"
    status_box = "\n".join([box_display, f"| {status_bar} |", box_display])

    return header + status_box

def run_main_menu(version, settings_obj):
    if settings_obj is None:
        cu.print_error("Invalid settings object provided.", False)
        return
    
    printable_header = _get_menu_info(version)
    while True:
        cu.clear_screen()
        cu.print_header(printable_header)
        selected_option = choice_prompt.get(
            "Select an option: ", 
            MENU_OPTIONS["top"], 
            bottom_toolbar=DEFAULT_TOOLBAR,
            nl_before=True,
            show_frame=True
        )

        if not _handle_main_menu_selection(selected_option, settings_obj):
            return
