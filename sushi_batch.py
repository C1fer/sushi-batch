import sys
import argparse
from colorama import init, Fore, Style
import files
import job_manager as jm
import console_utils as cu


# Handle actions when running directory-select tasks
def run_dir_modes_tasks(task, gui_enabled):
    src, dst = files.get_directories(gui_enabled)
    if src is not None and dst is not None:
        job_list = files.search_directories(src, dst, task)
        if job_list is not None:
            job_queue = jm.show_job_queue(job_list, task)

# Handle actions when running file-select tasks
def run_file_modes_tasks(task, gui_enabled):
    job_list = files.select_files(gui_enabled, task)
    if job_list is not None:
        jm.show_job_queue(job_list, task)


def main():
    # Initialize Colorama with auto style reset option
    init(autoreset=True)

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Sushi Batch Tool")
    parser.add_argument(
        "--no-gui",
        dest="no_gui",
        action="store_true",
        help="Disable all GUI functionality",
    )
    args = parser.parse_args()

    # St toggle to False if --no-gui flag is provided
    gui_enabled = False if args.no_gui else True

    while True:
        print(
            f"""\n{Fore.CYAN}Sushi Batch Tool{Style.RESET_ALL}
        1) Audio-based Sync  (Directory Select)
        2) Video-based Sync  (Directory Select) 
        3) Audio-based Sync  (Files Select)
        4) Video-based Sync  (Files Select) 
        5) Job Queue
        6) Exit"""
        )
        choice = cu.get_choice(range(1, 7))
        cu.clear_screen()

        match choice:
            case 1:
                print(f"{Fore.CYAN}Audio-based Sync (Directory mode)")
                run_dir_modes_tasks("aud-sync-dir", gui_enabled)
            case 2:
                print(f"{Fore.CYAN}Video-based Sync (Directory mode)")
                run_dir_modes_tasks("vid-sync-dir", gui_enabled)
            case 3:
                print(f"{Fore.CYAN}Audio-based Sync (Single-file mode)")
                run_file_modes_tasks("aud-sync-fil", gui_enabled)
            case 4:
                print(f"{Fore.CYAN}Video-based Sync (Single-file mode)")
                run_file_modes_tasks("vid-sync-fil", gui_enabled)
            case 5:
                if len(jm.job_queue[0]) == 0:
                    print(f"{Fore.LIGHTRED_EX}No jobs queued!")
                else:
                    jm.show_job_queue(task="job-queue")
            case 6:
                # Check if queue is empty before exiting
                if len(jm.job_queue[0]) == 0:
                    sys.exit()
                else:
                    if cu.confirm_action("Exiting will clear the job queue. Are you sure? (Y/N): "):
                        sys.exit()


if __name__ == "__main__":
    main()
