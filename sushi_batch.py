import sys
import files
import job_manager as jm
import console_utils as cu
import queue_data as qd

try:
    import sushi
    from art import text2art
except ImportError:
    cu.print_error("Install all requirements before running the tool")
    sys.exit(1)


# Handle actions when running directory-select tasks
def run_dir_modes_tasks(task):
    src, dst = files.get_directories()
    if src is not None and dst is not None:
        job_list = files.search_directories(src, dst, task)
        if job_list is not None:
            jm.handle_details_options(job_list, task)


# Handle actions when running file-select tasks
def run_file_modes_tasks(task):
    job_list = files.select_files(task)
    if job_list is not None:
        jm.handle_details_options(job_list, task)


def print_menu():
    cu.clear_screen()
    header = text2art("Sushi   Batch   Tool") 
    print(f"{cu.fore.CYAN}{header}")
    print("1) Audio-based Sync  (Directory Select) \n2) Video-based Sync  (Directory Select) \n3) Audio-based Sync  (File Select) \n4) Video-based Sync  (File Select) \n5) Job Queue \n6) Exit  ")


def main():

    # Exit with error message if FFmpeg is not found
    if not cu.is_ffmpeg_installed():
        cu.print_error("FFmpeg is not installed! \nAdd FFmpeg to PATH or copy the binary to this folder.")
        sys.exit(1)

    # Load queue contents on startup
    jm.job_queue = qd.load_list_data()

    while True:
        # Allow mode selection only if FFmpeg is found
        print_menu()
        selected_option = cu.get_choice(range(1, 7))
        cu.clear_screen()
        match selected_option:
            case 1:
                print(f"{cu.fore.CYAN}Audio-based Sync (Directory mode)")
                run_dir_modes_tasks("aud-sync-dir")
            case 2:
                print(f"{cu.fore.CYAN}Video-based Sync (Directory mode)")
                run_dir_modes_tasks("vid-sync-dir")
            case 3:
                print(f"{cu.fore.CYAN}Audio-based Sync (File-select mode)")
                run_file_modes_tasks("aud-sync-fil")
            case 4:
                print(f"{cu.fore.CYAN}Video-based Sync (File-select mode)")
                run_file_modes_tasks("vid-sync-fil")
            case 5:
                if len(jm.job_queue) == 0:
                    cu.print_error("No jobs queued!")
                else:
                    jm.handle_queue_options()
            case 6:
                    sys.exit(0)
                    

if __name__ == "__main__":
    main()
