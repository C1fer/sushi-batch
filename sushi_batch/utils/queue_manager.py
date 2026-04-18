from random import choice

from ..models.job_queue import JobQueue
from ..models.enums import JobSelection, Task
from ..models import settings as s

from ..external.mkv_merge import MKVMerge

from . import console_utils as cu
from .prompts import choice_prompt, confirm_prompt
from .queue_themes import QUEUE_RENDERERS

MAIN_QUEUE_OPTIONS= {
    "top": [
        (1, "Run jobs"),    
        (2, "Remove jobs"),
        (3, "Merge completed video jobs"),
        (4, "Go back"),
    ],
    "sub_run": [
        (1, "All pending"),
        (2, "Selected"),
        (3, "Go back"),
    ],
    "sub_remove": [
        (1, "All"),
        (2, "Completed and failed"),
        (3, "Selected"),
        (4, "Go back"),
    ],
}

TEMP_QUEUE_OPTIONS= {
    "top": [
        (1, "Run and add to main queue"),    
        (2, "Queue without running"),
        (3, "Return to main menu"),
    ],
    "sub_run_add": [
        (1, "All"),
        (2, "Selected"),
        (3, "Go back"),
    ],
}

TO_ADD_SELECTED_PROMPT = "Select which jobs to queue:"
TO_REMOVE_SELECTED_PROMPT = "Select which jobs to remove from queue:"
TO_RUN_SELECTED_PROMPT = "Select which jobs to run:"

main_queue = JobQueue()

def _show_continue_confirmation(jobs, is_removing=False):
    """Show confirmation prompt after adding jobs to main queue."""
    count = len(jobs)
    job_count = "1 job" if count == 1 else f"{count} jobs"
    action = "removed from" if is_removing else "added to"
    input(f"\n{cu.fore.LIGHTGREEN_EX}{job_count} {action} queue. Press Enter to continue...")

def show_queue(queue, current_task):
    """Display the current job queue with status and options.
        Theme is chosen from settings.
    """
    cu.clear_screen()
    title = "Job Queue" if current_task == Task.JOB_QUEUE else "Jobs"
    cu.print_header(f"{title}")
    
    renderer = QUEUE_RENDERERS.get(s.config.queue_theme, lambda q, t: cu.print_error("Invalid queue theme selected."))
    renderer(queue, current_task)
    
    

def main_queue_options(task):
    def _handle_run_options():
        run_choice = choice_prompt.get(message=TO_RUN_SELECTED_PROMPT, options=MAIN_QUEUE_OPTIONS["sub_run"], nl_before=False)
        match run_choice:
            case 1 if confirm_prompt.get():
                main_queue.run_jobs(JobSelection.ALL)
            case 2:
                selected_jobs = main_queue.select_jobs(prompt_message=TO_RUN_SELECTED_PROMPT)
                if selected_jobs and confirm_prompt.get():
                    main_queue.run_jobs(selected_jobs)

    def _handle_remove_options():
        remove_choice = choice_prompt.get(message=TO_REMOVE_SELECTED_PROMPT, options=MAIN_QUEUE_OPTIONS["sub_remove"], nl_before=False)
        match remove_choice:
            case 1 if confirm_prompt.get():
                main_queue.clear(trigger_file_cleanup=True)
                cu.print_success("All jobs removed from queue.")
            case 2 if confirm_prompt.get():
                main_queue.clear_completed_and_failed_jobs()
            case 3:
                selected_jobs = main_queue.select_jobs(prompt_message=TO_REMOVE_SELECTED_PROMPT)
                if selected_jobs and confirm_prompt.get():
                    main_queue.remove_jobs(selected_jobs)
                    _show_continue_confirmation(selected_jobs, is_removing=True)
           

    while True:
        show_queue(main_queue.contents, task)
        
        top_lvl_choice = choice_prompt.get(options=MAIN_QUEUE_OPTIONS["top"])
        match top_lvl_choice:
            case 1:
                _handle_run_options()
            case 2:
                _handle_remove_options()
                if not main_queue.contents:
                    break
            case 3 if confirm_prompt.get():
                if MKVMerge.is_installed:
                    main_queue.merge_completed_video_tasks(main_queue.contents)
                else:
                    cu.print_error("\nMKVMerge could not be found!")
            case _:
                break


def temp_queue_options(temp_queue, task):
    """Handle options for the temporary job queue created after file selection."""
    def _run_and_queue_all():
        main_queue.add_jobs(JobSelection.ALL, temp_queue.contents, task)
        temp_queue.run_jobs(JobSelection.ALL)
        return True

    def _queue_without_running_all():
        main_queue.add_jobs(JobSelection.ALL, temp_queue.contents, task)
        _show_continue_confirmation(temp_queue.contents)
        return True


    def _handle_run_and_queue_multiple():
        run_choice = choice_prompt.get(message=TO_RUN_SELECTED_PROMPT, options=TEMP_QUEUE_OPTIONS["sub_run_add"], nl_before=False)
        match run_choice:
            case 1 if confirm_prompt.get():
                return _run_and_queue_all()
            case 2:
                selected_jobs = temp_queue.select_jobs(prompt_message=TO_RUN_SELECTED_PROMPT)
                if selected_jobs and confirm_prompt.get():
                    main_queue.add_jobs(selected_jobs, temp_queue.contents, task)
                    temp_queue.run_jobs(selected_jobs)
                    return True

    def _handle_queue_without_running_multiple():
        add_choice = choice_prompt.get(message=TO_ADD_SELECTED_PROMPT, options=TEMP_QUEUE_OPTIONS["sub_run_add"], nl_before=False)
        match add_choice:
            case 1:
                return _queue_without_running_all()
            case 2:
                selected_jobs = temp_queue.select_jobs(prompt_message=TO_ADD_SELECTED_PROMPT)
                if selected_jobs and confirm_prompt.get():
                    main_queue.add_jobs(selected_jobs, temp_queue.contents, task)
                    _show_continue_confirmation(selected_jobs)
                    return True

    while True:
        show_queue(temp_queue.contents, task)
        is_single_job = len(temp_queue.contents) == 1
        
        top_lvl_choice = choice_prompt.get(options=TEMP_QUEUE_OPTIONS["top"])
        match top_lvl_choice:
            case 1:
                exit_loop = _run_and_queue_all() if is_single_job else _handle_run_and_queue_multiple()
                if exit_loop:
                    break
            case 2:
                exit_loop =_queue_without_running_all() if is_single_job else _handle_queue_without_running_multiple()
                if exit_loop:
                    break
            case 3:
                break
