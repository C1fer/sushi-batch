from .utils import utils
utils.check_required_packages() # Check if required packages are installed

import sys

from art import text2art

from .utils import console_utils as cu
from .utils import file_utils
from .utils import queue_manager as qm
from .models import settings as s
from .models.enums import Task
from .external.ffmpeg import FFmpeg
from .models.job_queue import JobQueue

VERSION = "0.2.0"

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

def show_main_menu():
    options = {
        "1": "Video-based Sync  (Directory Select)",
        "2": "Video-based Sync  (File Select)",
        "3": "Audio-based Sync  (Directory Select)",
        "4": "Audio-based Sync  (File Select)",
        "5": "Show Job Queue",
        "6": "Show Settings",
        "7": "Clear Logs",
        "8": "Exit",
    }

    header = text2art("Sushi Batch") + f"Version: {VERSION}"

    cu.clear_screen()
    cu.print_header(header)
    cu.show_menu_options(options)


def main():
    if not FFmpeg.is_installed:
        cu.print_error("FFmpeg could not be found! \nInstall or add the program to PATH before running the tool", False)
        sys.exit(1)

    # Load settings and queue contents on startup
    try:
        s.config.handle_load()
        qm.main_queue.load()
    except Exception as e:
        cu.print_error(f"Error initializing app: {e}")

    sync_tasks = {
        1: (Task.VIDEO_SYNC_DIR, "Video-based Sync (Directory mode)"),
        2: (Task.VIDEO_SYNC_FIL, "Video-based Sync (File-select mode)"),
        3: (Task.AUDIO_SYNC_DIR, "Audio-based Sync (Directory mode)"),
        4: (Task.AUDIO_SYNC_FIL, "Audio-based Sync (File-select mode)"),
    } 

    while True:
        show_main_menu()
        selected_option = cu.get_choice(1, 8)
        
        if selected_option not in (7, 8):
            cu.clear_screen()   

        match selected_option:
            case 1 | 2 | 3 | 4:
                task, header = sync_tasks[selected_option]
                cu.print_header(header)
                handle_sync_option_selected(task)
            case 5:
                if qm.main_queue.contents:
                    qm.main_queue_options(Task.JOB_QUEUE)
                else:
                    cu.print_error("No jobs queued!")
            case 6:
                s.config.handle_options()
            case 7:
                if cu.confirm_action():
                    utils.clear_logs(s.config.data_path)
                    cu.print_success("Logs cleared.")
            case 8:
                sys.exit(0)

    
if __name__ == "__main__":
    main()
