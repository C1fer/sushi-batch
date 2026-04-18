from ..models.job_queue import JobQueue
from ..models.enums import JobSelection, QueueTheme, Task
from ..models import settings as s

from ..external.mkv_merge import MKVMerge

from . import console_utils as cu
from .prompts import choice_prompt, confirm_prompt
from .queue_themes import QUEUE_RENDERERS

MAIN_QUEUE_OPTIONS = [
    (1, "Start queue"),
    (2, "Run selected jobs"),
    (3, "Remove selected jobs"),
    (4, "Merge video with synced sub on completed jobs"),
    (5, "Clear queue"),
    (6, "Clear completed and failed jobs"),
    (7, "Return to main menu"),
]

TEMP_QUEUE_OPTIONS = [
    (1, "Run all jobs"),
    (2, "Run selected jobs"),
    (3, "Add all jobs to queue"),
    (4, "Add selected jobs to queue"),
    (5, "Return to main menu"),
]

TO_ADD_SELECTED_PROMPT = "Select jobs to add to the queue:"
TO_REMOVE_SELECTED_PROMPT = "Select jobs to remove from queue:"
TO_RUN_SELECTED_PROMPT = "Select jobs to run:"

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
    while True:
        show_queue(main_queue.contents, task)
        
        choice = choice_prompt.get(options=MAIN_QUEUE_OPTIONS)
        match choice:
            case 1 if confirm_prompt.get():
                main_queue.run_jobs(JobSelection.ALL)
            case 2:
                selected_jobs = main_queue.select_jobs(prompt_message=TO_RUN_SELECTED_PROMPT)
                if selected_jobs and confirm_prompt.get():
                    main_queue.run_jobs(selected_jobs)
            case 3:
                selected_jobs = main_queue.select_jobs(prompt_message=TO_REMOVE_SELECTED_PROMPT)
                if selected_jobs and confirm_prompt.get():
                    main_queue.remove_jobs(selected_jobs)
                    _show_continue_confirmation(selected_jobs, is_removing=True)
                    if not main_queue.contents:
                        break
            case 4 if confirm_prompt.get():
                if MKVMerge.is_installed:
                    main_queue.merge_completed_video_tasks(main_queue.contents)
                else:
                    cu.print_error("\nMKVMerge could not be found!")
            case 5 if confirm_prompt.get():
                main_queue.clear()
                cu.print_success("Queue cleared.")
                break
            case 6 if confirm_prompt.get():
                main_queue.clear_completed_jobs()
                if not main_queue.contents:
                    break
            case 7:
                break

def temp_queue_options(temp_queue, task):
    """Handle options for the temporary job queue returned after file selection."""
    while True:
        show_queue(temp_queue.contents, task)
       
        choice = choice_prompt.get(options=TEMP_QUEUE_OPTIONS)
        match choice:
            case 1 if confirm_prompt.get():
                main_queue.add_jobs(JobSelection.ALL, temp_queue.contents, task)
                temp_queue.run_jobs(JobSelection.ALL)
                break
            case 2:
                selected_jobs = temp_queue.select_jobs(prompt_message=TO_RUN_SELECTED_PROMPT)
                if selected_jobs and confirm_prompt.get():
                    main_queue.add_jobs(selected_jobs, temp_queue.contents, task)
                    temp_queue.run_jobs(selected_jobs)
                    break
            case 3 if confirm_prompt.get():
                main_queue.add_jobs(JobSelection.ALL, temp_queue.contents, task)
                _show_continue_confirmation(temp_queue.contents)
                break
            case 4:
                selected_jobs = temp_queue.select_jobs(prompt_message=TO_ADD_SELECTED_PROMPT)
                if selected_jobs and confirm_prompt.get():
                    main_queue.add_jobs(selected_jobs, temp_queue.contents, task)
                    _show_continue_confirmation(selected_jobs)
                    break
            case 5 if confirm_prompt.get():
                break
