import sys
import argparse
import files
import job_manager as jm
import console_utils as cu


# Handle actions when running directory-select tasks
def run_dir_modes_tasks(task, gui_enabled):
    src, dst = files.get_directories(gui_enabled)
    if src is not None and dst is not None:
        job_list = files.search_directories(src, dst, task)
        if job_list is not None:
            jm.show_job_list(job_list, task)


# Handle actions when running file-select tasks
def run_file_modes_tasks(task, gui_enabled):
    job_list = files.select_files(gui_enabled, task)
    if job_list is not None:
        jm.show_job_list(job_list, task)


def print_menu():
    return print(
        f"""\n{cu.fore.CYAN}Sushi Batch Tool{cu.style_reset}
        1) Audio-based Sync  (Directory Select)
        2) Video-based Sync  (Directory Select) 
        3) Audio-based Sync  (Files Select)
        4) Video-based Sync  (Files Select) 
        5) Job Queue
        6) Exit"""
    )


# Parse command-line arguments
def parse_args():
    parser = argparse.ArgumentParser(description="Sushi Batch Tool")
    parser.add_argument(
        "--no-gui",
        dest="no_gui",
        action="store_true",
        help="Disable all GUI functionality",
    )
    args = parser.parse_args()
    return args.no_gui


def main():
    # Exit with error message if FFmpeg is not found
    if not cu.is_ffmpeg_installed():
        print_error(
            "FFmpeg is not installed! \nAdd FFmpeg to PATH or copy the binary to this folder."
        )
        sys.exit()

    # Set toggle to False if --no-gui flag is provided
    gui_enabled = not parse_args()

    while True:
        # Allow mode selection only if FFmpeg is found
        print_menu()
        selected_option = cu.get_choice(range(1, 7))
        cu.clear_screen()
        match selected_option:
            case 1:
                print(f"{cu.fore.CYAN}Audio-based Sync (Directory mode)")
                run_dir_modes_tasks("aud-sync-dir", gui_enabled)
            case 2:
                print(f"{cu.fore.CYAN}Video-based Sync (Directory mode)")
                run_dir_modes_tasks("vid-sync-dir", gui_enabled)
            case 3:
                print(f"{cu.fore.CYAN}Audio-based Sync (File-select mode)")
                run_file_modes_tasks("aud-sync-fil", gui_enabled)
            case 4:
                print(f"{cu.fore.CYAN}Video-based Sync (File-select mode)")
                run_file_modes_tasks("vid-sync-fil", gui_enabled)
            case 5:
                if len(jm.job_queue) == 0:
                    cu.print_error("No jobs queued!")
                else:
                    jm.show_job_list(task="job-queue")
            case 6:
                # Check if queue is empty before exiting
                if len(jm.job_queue) > 0:
                    if cu.confirm_action(
                        f"{cu.fore.LIGHTYELLOW_EX}Exiting will clear the job queue. Are you sure? (Y/N): "
                    ):
                        sys.exit()
                    cu.clear_screen()
                else:
                    sys.exit()


if __name__ == "__main__":
    main()
