from ..models.job_queue import JobQueue
from ..models.enums import JobSelection, Task, Status
from ..models import settings as s

from ..external.mkv_merge import MKVMerge

from ..utils import console_utils as cu
from ..utils.prompts import choice_prompt, confirm_prompt
from .queue_themes import QUEUE_RENDERERS

MAIN_QUEUE_OPTIONS= {
    "top": [
        (1, "Run Jobs"),    
        (2, "Remove Jobs"),
        (3, "Merge Video Jobs"),
        (4, "Go Back"),
    ],
    "sub_run": [
        (1, "All Pending"),
        (2, "Selected"),
        (3, "Go Back"),
    ],
    "sub_remove": [
        (1, "All"),
        (2, "Completed and Failed"),
        (3, "Selected"),
        (4, "Go Back"),
    ],
    "sub_merge": [
        (1, "All Completed"),
        (2, "Selected"),
        (3, "Go Back"),
    ]
}

TEMP_QUEUE_OPTIONS= {
    "top": [
        (1, "Run and Add to Main Queue"),    
        (2, "Queue Without Running"),
        (3, "Return to Main Menu"),
    ],
    "sub_run_add": [
        (1, "All"),
        (2, "Selected"),
        (3, "Go Back"),
    ],
}

TO_ADD_SELECTED_PROMPT = "Select which jobs to queue:"
TO_REMOVE_SELECTED_PROMPT = "Select which jobs to remove from queue:"
TO_RUN_SELECTED_PROMPT = "Select which jobs to run:"
TO_MERGE_SELECTED_PROMPT = "Select which video jobs to merge:"

main_queue = JobQueue()

def _show_continue_confirmation(jobs, is_removing=False):
    """Show confirmation prompt after adding jobs to main queue."""
    count = len(jobs)
    job_count = "1 job" if count == 1 else f"{count} jobs"
    action = "removed from" if is_removing else "added to"
    input(f"\n{cu.fore.LIGHTGREEN_EX}{job_count} {action} queue. Press Enter to continue...")

def _show_queue_items(queue, current_task):
    """Display the current job queue in the selected theme. Theme is chosen from settings."""
    cu.clear_screen()
    title = "Job Queue" if current_task == Task.JOB_QUEUE else "Jobs"
    cu.print_header(f"{title}")
    
    renderer = QUEUE_RENDERERS.get(s.config.queue_theme, lambda q, t: cu.print_error("Invalid queue theme selected."))
    renderer(queue, current_task)
     
def show_main_queue(task):
    """Display the main job queue and handle user interactions."""
    def _handle_run_options():
        run_choice = choice_prompt.get(message=TO_RUN_SELECTED_PROMPT, options=MAIN_QUEUE_OPTIONS["sub_run"], nl_before=False)
        match run_choice:
            case 1 if confirm_prompt.get():
                _jobs = [job for job in main_queue.contents if job.sync_status == Status.PENDING]
                main_queue.run_jobs(_jobs)
            case 2:
                selected_jobs = main_queue.select_jobs(
                    prompt_message=TO_RUN_SELECTED_PROMPT,
                    filter_fn=lambda j: j.sync_status == Status.PENDING,
                )
                if selected_jobs and confirm_prompt.get("Run selected jobs?"):
                    main_queue.run_jobs(selected_jobs)

    def _handle_remove_options():
        remove_choice = choice_prompt.get(message=TO_REMOVE_SELECTED_PROMPT, options=MAIN_QUEUE_OPTIONS["sub_remove"], nl_before=False)
        match remove_choice:
            case 1 if confirm_prompt.get("Clear job queue?", destructive=True):
                main_queue.clear(trigger_file_cleanup=True)
                cu.print_success("All jobs removed from queue.")
            case 2 if confirm_prompt.get(destructive=True):
                main_queue.clear_completed_and_failed_jobs()
            case 3:
                selected_jobs = main_queue.select_jobs(prompt_message=TO_REMOVE_SELECTED_PROMPT)
                if selected_jobs and confirm_prompt.get("Remove selected jobs from queue?", destructive=True):
                    main_queue.remove_jobs(selected_jobs)
                    _show_continue_confirmation(selected_jobs, is_removing=True)

    def _handle_merge_options():
        if not  MKVMerge.is_installed:
            cu.print_error("\nMKVMerge could not be found! Install MKVMerge to enable merging functionality.")
            return
        
        merge_choice = choice_prompt.get(message=TO_MERGE_SELECTED_PROMPT, options=MAIN_QUEUE_OPTIONS["sub_merge"], nl_before=False)
        match merge_choice:
            case 1:
                main_queue.merge_completed_video_jobs(JobSelection.ALL)
            case 2:
                selected_jobs = main_queue.select_jobs(
                    prompt_message=TO_MERGE_SELECTED_PROMPT,
                    filter_fn=lambda j: (
                        j.sync_status == Status.COMPLETED
                        and j.task in (Task.VIDEO_SYNC_DIR, Task.VIDEO_SYNC_FIL)
                        and not j.merged
                    ),
                )
                if selected_jobs and confirm_prompt.get("Merge selected jobs?"):
                    main_queue.merge_completed_video_jobs(JobSelection.SELECTED, selected_jobs)

    while True:
        _show_queue_items(main_queue.contents, task)
        
        top_lvl_choice = choice_prompt.get(options=MAIN_QUEUE_OPTIONS["top"])
        match top_lvl_choice:
            case 1:
                _handle_run_options()
            case 2:
                _handle_remove_options()
                if not main_queue.contents:
                    break
            case 3:
                _handle_merge_options()
            case _:
                break

def show_temp_queue(temp_queue, task):
    """Handle options for the temporary job queue created after file selection."""
    def _run_and_queue_all():
        main_queue.add_jobs(temp_queue.contents, task)
        temp_queue.run_jobs(temp_queue.contents)
        return True

    def _queue_without_running_all():
        main_queue.add_jobs(temp_queue.contents, task)
        _show_continue_confirmation(temp_queue.contents)
        return True


    def _handle_run_and_queue_multiple():
        run_choice = choice_prompt.get(message=TO_RUN_SELECTED_PROMPT, options=TEMP_QUEUE_OPTIONS["sub_run_add"], nl_before=False)
        match run_choice:
            case 1 if confirm_prompt.get():
                return _run_and_queue_all()
            case 2:
                selected_jobs = temp_queue.select_jobs(prompt_message=TO_RUN_SELECTED_PROMPT)
                if selected_jobs and confirm_prompt.get("Run selected jobs and add to main queue?", nl_after=True):
                    main_queue.add_jobs(selected_jobs, task)
                    temp_queue.run_jobs(selected_jobs)
                    return True

    def _handle_queue_without_running_multiple():
        add_choice = choice_prompt.get(message=TO_ADD_SELECTED_PROMPT, options=TEMP_QUEUE_OPTIONS["sub_run_add"], nl_before=False)
        match add_choice:
            case 1:
                return _queue_without_running_all()
            case 2:
                selected_jobs = temp_queue.select_jobs(prompt_message=TO_ADD_SELECTED_PROMPT)
                if selected_jobs and confirm_prompt.get("Add selected jobs to main queue?", nl_after=True):
                    main_queue.add_jobs(selected_jobs, task)
                    _show_continue_confirmation(selected_jobs)
                    return True

    while True:
        _show_queue_items(temp_queue.contents, task)
        is_single_job = len(temp_queue.contents) == 1
        
        top_lvl_choice = choice_prompt.get(options=TEMP_QUEUE_OPTIONS["top"])
        match top_lvl_choice:
            case 1:
                exit_loop = _run_and_queue_all() if is_single_job else _handle_run_and_queue_multiple()
                if exit_loop:
                    return True
            case 2:
                exit_loop =_queue_without_running_all() if is_single_job else _handle_queue_without_running_multiple()
                if exit_loop:
                    return True
            case 3:
                return False
