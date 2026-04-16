from ..models.job_queue import JobQueue
from ..models.enums import JobSelection, QueueTheme, Task, Status
from ..models import settings as s

from ..external.mkv_merge import MKVMerge

from . import console_utils as cu


main_queue = JobQueue()

def _status_style(status):
    """Return display metadata for a job status."""
    match status:
        case Status.COMPLETED:
            return (cu.fore.LIGHTGREEN_EX, "Completed", "+", cu.fore.GREEN)
        case Status.FAILED:
            return (cu.fore.LIGHTRED_EX, "Failed", "x", cu.fore.RED)
        case _:
            return (cu.fore.LIGHTBLACK_EX, "Pending", "~", cu.fore.LIGHTBLACK_EX)

def show_classic_queue(queued_jobs, current_task):
    """ Show Job List contents (Classic Theme) """
    for job in queued_jobs:
        job.idx = queued_jobs.index(job) + 1
        print(f"\n{cu.fore.LIGHTBLACK_EX}Job {job.idx}")
        print(f"{cu.fore.LIGHTBLUE_EX}Source file: {job.src_file}")
        print(f"{cu.fore.LIGHTYELLOW_EX}Destination file: {job.dst_file}")

        if job.sub_file is not None:
            print(f"{cu.fore.LIGHTCYAN_EX }Subtitle file: {job.sub_file}")

        if job.src_aud_display is not None:
            print(f"{cu.fore.LIGHTMAGENTA_EX}Source Audio Track: {job.src_aud_display}")

        if job.src_sub_display is not None:
            print(f"{cu.fore.LIGHTCYAN_EX}Source Subtitle Track: {job.src_sub_display}")

        if job.dst_aud_display is not None:
            print(f"{cu.fore.YELLOW}Destination Audio Track: {job.dst_aud_display}")

        if job.src_aud_id is not None and job.src_aud_display is None:
            print(f"{cu.fore.LIGHTMAGENTA_EX}Source Audio Track ID: {job.src_aud_id}")

        if job.src_sub_id is not None and job.src_sub_display is None:
            print(f"{cu.fore.LIGHTCYAN_EX}Source Subtitle Track ID: {job.src_sub_id}")

        if job.dst_aud_id is not None and job.dst_aud_display is None:
            print(f"{cu.fore.YELLOW}Destination Audio Track ID: {job.dst_aud_id}")

        if current_task == Task.JOB_QUEUE: 
            match job.status:
                case Status.PENDING:
                    print(f"{cu.fore.LIGHTBLACK_EX}Status: Pending")
                case Status.COMPLETED:
                    print(f"{cu.fore.LIGHTGREEN_EX}Status: Completed")
                    print(f"{cu.fore.GREEN}Average Shift: {job.result}")
                case Status.FAILED:
                    print(f"{cu.fore.LIGHTRED_EX}Status: Failed")
                    print(f"{cu.fore.RED}Error: {job.result}")

            match job.merged:
                case True:
                    print(f"{cu.fore.LIGHTGREEN_EX}Merged: Yes")
                case False:
                    print(f"{cu.fore.LIGHTBLACK_EX}Merged: No")


def show_card_queue(queued_jobs, current_task):
    """Show job list using card-style blocks (Option 2)."""
    for idx, job in enumerate(queued_jobs, start=1):
        job.idx = idx
        status_color, status_label, status_icon, detail_color = _status_style(job.status)

        print(f"\n{cu.fore.LIGHTBLUE_EX}+- Job {idx} [{status_color}{status_icon} {status_label}{cu.fore.LIGHTBLUE_EX}]")
        print(f"{cu.fore.LIGHTBLACK_EX}| Source      : {cu.fore.LIGHTBLUE_EX}{job.src_file}")
        print(f"{cu.fore.LIGHTBLACK_EX}| Destination : {cu.fore.LIGHTYELLOW_EX}{job.dst_file}")

        if job.sub_file is not None:
            print(f"{cu.fore.LIGHTBLACK_EX}| Subtitle    : {cu.fore.LIGHTCYAN_EX}{job.sub_file}")

        src_audio = job.src_aud_display if job.src_aud_display is not None else job.src_aud_id
        src_sub = job.src_sub_display if job.src_sub_display is not None else job.src_sub_id
        dst_audio = job.dst_aud_display if job.dst_aud_display is not None else job.dst_aud_id

        if src_audio is not None:
            print(f"{cu.fore.LIGHTBLACK_EX}| Src Audio   : {cu.fore.LIGHTMAGENTA_EX}{src_audio}")
        if src_sub is not None:
            print(f"{cu.fore.LIGHTBLACK_EX}| Src Subtitle: {cu.fore.LIGHTCYAN_EX}{src_sub}")
        if dst_audio is not None:
            print(f"{cu.fore.LIGHTBLACK_EX}| Dst Audio   : {cu.fore.YELLOW}{dst_audio}")

        if current_task == Task.JOB_QUEUE:
            print(f"{cu.fore.LIGHTBLACK_EX}| Status      : {status_color}{status_label}")
            if job.status == Status.COMPLETED:
                print(f"{cu.fore.LIGHTBLACK_EX}| Avg Shift   : {detail_color}{job.result}")
            elif job.status == Status.FAILED:
                print(f"{cu.fore.LIGHTBLACK_EX}| Error       : {detail_color}{job.result}")
            merged_label = "Yes" if job.merged else "No"
            merged_color = cu.fore.LIGHTGREEN_EX if job.merged else cu.fore.LIGHTBLACK_EX
            print(f"{cu.fore.LIGHTBLACK_EX}+ Merged      : {merged_color}{merged_label}")


def show_yaml_queue(queued_jobs, current_task):
    """Show job list in a YAML/config style format (Option 4)."""
    for idx, job in enumerate(queued_jobs, start=1):
        job.idx = idx
        status_color, status_label, _, detail_color = _status_style(job.status)

        print(f"\n{cu.fore.LIGHTBLUE_EX}Job {idx}:")
        print(f"{cu.fore.LIGHTBLACK_EX}  source_file: {cu.fore.LIGHTBLUE_EX}{job.src_file}")
        print(f"{cu.fore.LIGHTBLACK_EX}  destination_file: {cu.fore.LIGHTYELLOW_EX}{job.dst_file}")
        
        if job.sub_file is not None:
            print(f"{cu.fore.LIGHTBLACK_EX}  subtitle_file: {cu.fore.LIGHTCYAN_EX}{job.sub_file}")

        if job.task in (Task.VIDEO_SYNC_DIR, Task.VIDEO_SYNC_FIL):
            src_audio = job.src_aud_display if job.src_aud_display is not None else job.src_aud_id
            src_sub = job.src_sub_display if job.src_sub_display is not None else job.src_sub_id
            dst_audio = job.dst_aud_display if job.dst_aud_display is not None else job.dst_aud_id

            print(f"{cu.fore.LIGHTBLACK_EX}  tracks:")
            print(f"{cu.fore.LIGHTBLACK_EX}    source_audio: {cu.fore.LIGHTMAGENTA_EX}{src_audio if src_audio is not None else 'null'}")
            print(f"{cu.fore.LIGHTBLACK_EX}    source_subtitle: {cu.fore.LIGHTCYAN_EX}{src_sub if src_sub is not None else 'null'}")
            print(f"{cu.fore.LIGHTBLACK_EX}    destination_audio: {cu.fore.YELLOW}{dst_audio if dst_audio is not None else 'null'}")

        if current_task == Task.JOB_QUEUE:
            print(f"{cu.fore.LIGHTBLACK_EX}  status: {status_color}{status_label.lower()}")
            if job.status == Status.COMPLETED:
                print(f"{cu.fore.LIGHTBLACK_EX}  average_shift: {detail_color}{job.result}")
            elif job.status == Status.FAILED:
                print(f"{cu.fore.LIGHTBLACK_EX}  error: {detail_color}{job.result}")
            merged_label = "true" if job.merged else "false"
            merged_color = cu.fore.LIGHTGREEN_EX if job.merged else cu.fore.LIGHTBLACK_EX
            print(f"{cu.fore.LIGHTBLACK_EX}  merged: {merged_color}{merged_label}")
    

def show_queue(queue, current_task):
    """Display the current job queue with status and options.
        Theme is chosen from settings.
    """
    cu.clear_screen()
    title = "Job Queue" if current_task == Task.JOB_QUEUE else "Jobs"
    cu.print_header(f"{title}")
    
    current_theme = s.config.queue_theme
    match current_theme:
        case QueueTheme.CLASSIC.value:
            show_classic_queue(queue, current_task)
        case QueueTheme.CARD.value:
            show_card_queue(queue, current_task)
        case QueueTheme.YAML.value:
            show_yaml_queue(queue, current_task)
        case _:
            cu.print_error(f"Unknown queue theme: {current_theme}")
            show_classic_queue(queue, current_task)


def main_queue_options(task):
    while True:
        options = {
            "1": "Start queue",
            "2": "Run selected jobs",
            "3": "Remove selected jobs",
            "4": "Merge video with synced sub on completed jobs",
            "5": "Clear queue",
            "6": "Clear completed and failed jobs",
            "7": "Return to main menu",
        }
        show_queue(main_queue.contents, task)
        cu.show_menu_options(options)

        choice = cu.get_choice(1, 7)

        match choice:
            case 1 if cu.confirm_action():
                main_queue.run_jobs(JobSelection.ALL)
            case 2:
                selected_jobs = main_queue.select_jobs("Select jobs to run (e.g: 1, 5-10): ")
                if selected_jobs and cu.confirm_action():
                    main_queue.run_jobs(selected_jobs)
            case 3:
                selected_jobs = main_queue.select_jobs("Select jobs to remove from queue (e.g: 1, 5-10): ")
                if selected_jobs and cu.confirm_action():
                    main_queue.remove_jobs(selected_jobs)
                    cu.print_success(f"{len(selected_jobs)} job(s) removed from queue.")
                    if not main_queue.contents:
                        break
            case 4 if cu.confirm_action():
                if MKVMerge.is_installed:
                    main_queue.merge_completed_video_tasks(main_queue.contents)
                else:
                    cu.print_error("\nMKVMerge could not be found!")
            case 5 if cu.confirm_action():
                main_queue.clear()
                cu.print_success("Queue cleared.")
                break
            case 6 if cu.confirm_action():
                main_queue.clear_completed_jobs()
                if not main_queue.contents:
                    break
            case 7:
                break


def temp_queue_options(temp_queue, task):
    """Handle options for the temporary job queue returned after file selection."""
    while True:
        options = {
            "1": "Run all jobs",
            "2": "Run selected jobs",
            "3": "Add all jobs to queue",
            "4": "Add selected jobs to queue",
            "5": "Return to main menu",
        }
        temp_queue.show(task)
        cu.show_menu_options(options)

        choice = cu.get_choice(1, 5)

        match choice:
            case 1 if cu.confirm_action():
                main_queue.add_jobs(JobSelection.ALL, temp_queue.contents, task)
                temp_queue.run_jobs(JobSelection.ALL)
                break
            case 2:
                selected_jobs = temp_queue.select_jobs("Select jobs to run (e.g: 1, 5-10): ")
                if selected_jobs and cu.confirm_action():
                    main_queue.add_jobs(selected_jobs, temp_queue.contents, task)
                    temp_queue.run_jobs(selected_jobs)
                    break
            case 3 if cu.confirm_action():
                main_queue.add_jobs(JobSelection.ALL, temp_queue.contents, task)
                cu.print_success(f"{len(temp_queue.contents)} job(s) added to queue.")
                break
            case 4:
                selected_jobs = temp_queue.select_jobs("Select jobs to add to the queue (e.g: 1, 5-10): ")
                if selected_jobs and cu.confirm_action():
                    main_queue.add_jobs(selected_jobs, temp_queue.contents, task)
                    cu.print_success(f"{len(selected_jobs)} job(s) added to queue.")
                    break
            case 5 if cu.confirm_action():
                break
