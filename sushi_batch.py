import sys
from importlib.util import find_spec

# Check if required packages are installed
packages = ["art", "colorama", "cv2", "sushi", "prettytable", "yaspin"]
for pkg in packages:
    if find_spec(pkg) is None:
        print(
            "\033[91m{}\033[00m".format(
                f"Package {pkg} is not installed. Install all dependencies before running the tool"
            )
        )
        sys.exit(1)

from art import text2art
import files
from enums import Task
import settings as s
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
        "6": "Settings",
        "7": "Exit",
    }
    cu.clear_screen()
    header = text2art("Sushi Batch Tool")
    cu.print_header(f"{header}")
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
    if not cu.is_app_installed("ffmpeg"):
        cu.print_error("FFmpeg could not be found! \nInstall or add the program to PATH before running the tool", False)
        sys.exit(1)

    # Load settings and queue contents on startup
    s.config.handle_load()
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
                if qm.main_queue.contents:
                    qm.main_queue_options(Task.JOB_QUEUE)
                else:
                    cu.print_error("No jobs queued!")
            case 6:
                s.config.handle_options()
            case 7:
                sys.exit(0)


if __name__ == "__main__":
    main()
