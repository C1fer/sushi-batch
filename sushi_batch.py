import sys
from importlib.util import find_spec

# Check if required packages are installed
packages = ["colorama", "sushi", "prettytable", "yaspin"]
for pkg in packages:
    if find_spec(pkg) is None:
        print(f"Package {pkg} is not installed! Install all requirements before running the tool")
        sys.exit(1)

import files
from enums import Task
from job_queue import JobQueue
import queue_manager as qm
import console_utils as cu


# Show main menu
def main_menu():
    options = {
        "1": "Audio-based Sync  (Directory Select)",
        "2": "Video-based Sync  (Directory Select)",
        "3": "Audio-based Sync  (File Select)",
        "4": "Video-based Sync  (File Select)",
        "5": "Job Queue",
        "6": "Exit",
    }
    cu.clear_screen()
    cu.print_header(f"{cu.app_logo}")
    cu.show_menu_options(options)


def run_modes(task):
    # Get jobs from file/folder selection
    if task in (Task.AUDIO_SYNC_DIR, Task.VIDEO_SYNC_DIR):
        src, dst = files.get_directories()
        if src is not None and dst is not None:
            jobs = files.search_directories(src, dst, task)
    else:
        jobs = files.select_files(task)

    # Show options if job list is not empty
    if jobs is not None:
        temp_queue = JobQueue(jobs)
        qm.temp_queue_options(temp_queue, task)


def main():
    # Exit with error message if FFmpeg is not found
    if not cu.is_ffmpeg_installed():
        cu.print_error(
            "FFmpeg could not be found. \nAdd the filepath to %PATH% or copy the binary to this folder."
        )
        sys.exit(1)

    # Load queue contents on startup
    qm.main_queue.load()

    # Allow mode selection only if FFmpeg is found
    while True:
        main_menu()
        selected_option = cu.get_choice(1, 7)
        cu.clear_screen()
        match selected_option:
            case 1:
                cu.print_header("Audio-based Sync (Directory mode)")
                run_modes(Task.AUDIO_SYNC_DIR)
            case 2:
                cu.print_header("Video-based Sync (Directory mode)")
                run_modes(Task.VIDEO_SYNC_DIR)
            case 3:
                cu.print_header("Audio-based Sync (File-select mode)")
                run_modes(Task.AUDIO_SYNC_FIL)
            case 4:
                cu.print_header("Video-based Sync (File-select mode)")
                run_modes(Task.VIDEO_SYNC_FIL)
            case 5:
                if not qm.main_queue.contents:
                    cu.print_error("No jobs queued!")
                else:
                    qm.main_queue_options(Task.JOB_QUEUE)
            case 6:
                sys.exit(0)


if __name__ == "__main__":
    main()
