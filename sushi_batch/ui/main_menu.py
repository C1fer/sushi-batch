from art import text2art

from ..models.enums import Task
from ..models.job_queue import JobQueue
from ..utils import console_utils as cu
from ..utils import file_utils
from ..utils import queue_manager as qm
from ..utils import utils
from ..utils.prompts import choice_prompt, confirm_prompt

from .settings_menu import show_settings_menu

MENU_OPTIONS = [
    (1, "Video-based Sync (Directory mode)"),
    (2, "Video-based Sync (File-select mode)"),
    (3, "Audio-based Sync (Directory mode)"),
    (4, "Audio-based Sync (File-select mode)"),
    (5, "View Job Queue"),
    (6, "Settings"),
    (7, "Clear Logs"),
    (8, "Exit"),
]

SYNC_TASK_DISPLAY = {
    1: (Task.VIDEO_SYNC_DIR, "Video-based Sync (Directory mode)"),
    2: (Task.VIDEO_SYNC_FIL, "Video-based Sync (File-select mode)"),
    3: (Task.AUDIO_SYNC_DIR, "Audio-based Sync (Directory mode)"),
    4: (Task.AUDIO_SYNC_FIL, "Audio-based Sync (File-select mode)"),
}


def handle_sync_option_selected(task):
    jobs = None

    if task in (Task.AUDIO_SYNC_DIR, Task.VIDEO_SYNC_DIR):
        src, dst = file_utils.get_directories()
        if src and dst:
            jobs = file_utils.search_directories(src, dst, task)
    else:
        jobs = file_utils.select_files(task)

    if jobs:
        qm.temp_queue_options(JobQueue(jobs), task)


def _handle_main_menu_selection(selected_option, settings_obj):
    match selected_option:
        case 1 | 2 | 3 | 4:
            task, header = SYNC_TASK_DISPLAY[selected_option]
            cu.print_header(header)
            handle_sync_option_selected(task)
        case 5:
            if qm.main_queue.contents:
                qm.main_queue_options(Task.JOB_QUEUE)
            else:
                cu.print_error("No jobs queued!")
        case 6:
            show_settings_menu(settings_obj)
        case 7:
            if confirm_prompt.get("Are you sure you want to clear the logs? This action cannot be undone. (Y/N): "):
                utils.clear_logs(settings_obj.data_path)
                cu.print_success("Logs cleared.")
        case 8:
            return False

    return True


def show_main_menu(version=None):
    version_str = f"Version: {version}" if version else ""
    header = text2art("Sushi Batch") + version_str

    cu.clear_screen()
    cu.print_header(header)


def run_main_menu(version, settings_obj):
    if settings_obj is None:
        cu.print_error("Invalid settings object provided.", False)
        return

    while True:
        show_main_menu(version)
        selected_option = choice_prompt.get("Select an option: ", MENU_OPTIONS, show_toolbar=True, show_frame=True)

        if selected_option not in (7, 8):
            cu.clear_screen()

        if not _handle_main_menu_selection(selected_option, settings_obj):
            return
