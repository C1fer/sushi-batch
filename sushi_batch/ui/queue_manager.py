from ..models.job_queue import JobQueue
from ..models.enums import JobSelection, Task, Status
from ..models import settings as s

from ..external.mkv_merge import MKVMerge

from ..utils import constants
from ..utils import console_utils as cu
from .prompts import confirm_prompt, choice_prompt
from .queue_themes import QUEUE_RENDERERS

MAIN_QUEUE_OPTIONS= {
    "top": [
        (1, "Run Jobs"),
        (2, "Run Jobs (Advanced Sushi Args)", lambda q: s.config.enable_sushi_advanced_args),
        (3, "Remove Jobs"),
        (4, "Merge Completed Video Jobs", lambda args: MKVMerge.is_installed and args["to_merge"]),
        (5, "Go Back"),
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
        (2, "Run and Add to Main Queue (Advanced Sushi Args)", lambda: s.config.enable_sushi_advanced_args),
        (3, "Queue Without Running"),
        (4, "Return to Main Menu"),
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

def get_queue_stats(queue = None, requested_key=None):    
    """Return summary statistics for the job queue, including total jobs, pending, completed, and failed counts."""
    _queue = queue if queue is not None else main_queue.contents
    _key = requested_key.lower() if requested_key else None
    
    match _key:
        case "total":
            return len(_queue)
        case "pending":
            return sum(1 for job in _queue if job.sync_status == Status.PENDING)
        case "completed":
            return sum(1 for job in _queue if job.sync_status == Status.COMPLETED)
        case "failed":
            return sum(1 for job in _queue if job.sync_status == Status.FAILED)

    return {
        "total": len(_queue),
        "pending": sum(1 for job in _queue if job.sync_status == Status.PENDING),
        "completed": sum(1 for job in _queue if job.sync_status == Status.COMPLETED),
        "failed": sum(1 for job in _queue if job.sync_status == Status.FAILED),
    }

def get_stats_bar(queue=None):
    """Generate a formatted status bar with per-field colors."""
    stats = get_queue_stats(queue)
    separator_classname = ("class:bottom-toolbar.sep", " | ")
    bar = [
        ("", " Sync Stats  ->    "), 
        ("class:bottom-toolbar.label", "Total: "),
        ("class:bottom-toolbar.total", str(stats["total"])),
        separator_classname,
        ("class:bottom-toolbar.label", "Pending: "),
        ("class:bottom-toolbar.pending", str(stats["pending"])),
        separator_classname,
        ("class:bottom-toolbar.label", "Completed: "),
        ("class:bottom-toolbar.completed", str(stats["completed"])),
        separator_classname,
        ("class:bottom-toolbar.label", "Failed: "),
        ("class:bottom-toolbar.failed", str(stats["failed"])),
    ]
    return bar, stats["pending"]

def show_main_queue(task):
    """Display the main job queue and handle user interactions."""
    def _handle_run_options(toolbar_stats=None, pending_count=None, use_advanced_sushi_args=False):
        if pending_count == 0:
            cu.print_warning("No pending jobs to run.")
            return

        run_choice = choice_prompt.get(message=TO_RUN_SELECTED_PROMPT, options=MAIN_QUEUE_OPTIONS["sub_run"], nl_before=False, bottom_toolbar=toolbar_stats)
        match run_choice:
            case 1 if confirm_prompt.get(bottom_toolbar=toolbar_stats):
                _jobs = [job for job in main_queue.contents if job.sync_status == Status.PENDING]
                main_queue.run_jobs(_jobs, use_advanced_sushi_args=use_advanced_sushi_args)
            case 2:
                selected_jobs = main_queue.select_jobs(
                    prompt_message=TO_RUN_SELECTED_PROMPT,
                    filter_fn=lambda j: j.sync_status == Status.PENDING,
                )
                if selected_jobs and confirm_prompt.get("Run selected jobs?", bottom_toolbar=toolbar_stats):
                    main_queue.run_jobs(selected_jobs, use_advanced_sushi_args=use_advanced_sushi_args)

    def _handle_remove_options(toolbar_stats=None):
        remove_choice = choice_prompt.get(message=TO_REMOVE_SELECTED_PROMPT, options=MAIN_QUEUE_OPTIONS["sub_remove"], nl_before=False, bottom_toolbar=toolbar_stats)
        match remove_choice:
            case 1 if confirm_prompt.get("Clear job queue?", destructive=True, bottom_toolbar=toolbar_stats):
                main_queue.clear(trigger_file_cleanup=True)
                cu.print_success("All jobs removed from queue.")
            case 2 if confirm_prompt.get(destructive=True, bottom_toolbar=toolbar_stats):
                main_queue.clear_completed_and_failed_jobs()
            case 3:
                selected_jobs = main_queue.select_jobs(prompt_message=TO_REMOVE_SELECTED_PROMPT)
                if selected_jobs and confirm_prompt.get("Remove selected jobs from queue?", destructive=True, bottom_toolbar=toolbar_stats):
                    main_queue.remove_jobs(selected_jobs)
                    _show_continue_confirmation(selected_jobs, is_removing=True)

    def _handle_merge_options(toolbar_stats=None):
        if not  MKVMerge.is_installed:
            cu.print_error("\nMKVMerge could not be found! Install MKVMerge to enable merging functionality.")
            return
        
        merge_choice = choice_prompt.get(message=TO_MERGE_SELECTED_PROMPT, options=MAIN_QUEUE_OPTIONS["sub_merge"], nl_before=False, bottom_toolbar=toolbar_stats)
        match merge_choice:
            case 1:
                main_queue.merge_completed_video_jobs(JobSelection.ALL)
            case 2:
                selected_jobs = main_queue.select_jobs(
                    prompt_message=TO_MERGE_SELECTED_PROMPT,
                    filter_fn=lambda j: (
                        j.sync_status == Status.COMPLETED
                        and j.task in constants.VIDEO_TASKS
                        and not j.merged
                    ),
                )
                if selected_jobs and confirm_prompt.get("Merge selected jobs?", bottom_toolbar=toolbar_stats):
                    main_queue.merge_completed_video_jobs(JobSelection.SELECTED, selected_jobs)
    
    while True:
        _show_queue_items(main_queue.contents, task)
        bottom_toolbar, pending_count = get_stats_bar()

        validations = {
            "to_merge": any(j for j in main_queue.contents if j.sync_status == Status.COMPLETED and j.task in constants.VIDEO_TASKS and not j.merged)
        }

        available_options = [
            opt[:2]
            for opt in MAIN_QUEUE_OPTIONS["top"]
            if (opt[2](validations) if len(opt) > 2 else True)
        ]
        
        top_lvl_choice = choice_prompt.get(options=available_options, bottom_toolbar=bottom_toolbar)
        match top_lvl_choice:
            case 1 | 2:
                _handle_run_options(toolbar_stats=bottom_toolbar, pending_count=pending_count, use_advanced_sushi_args=top_lvl_choice == 2)
            case 3:
                _handle_remove_options(toolbar_stats=bottom_toolbar)
                if not main_queue.contents:
                    break
            case 4:
                _handle_merge_options(toolbar_stats=bottom_toolbar)
            case _:
                break

def show_temp_queue(temp_queue, task):
    """Handle options for the temporary job queue created after file selection."""
    def _run_and_queue_all(use_advanced_sushi_args=False):
        main_queue.add_jobs(temp_queue.contents, task)
        temp_queue.run_jobs(temp_queue.contents, use_advanced_sushi_args=use_advanced_sushi_args)
        return True

    def _queue_without_running_all():
        main_queue.add_jobs(temp_queue.contents, task)
        _show_continue_confirmation(temp_queue.contents)
        return True

    def _handle_run_and_queue_multiple(use_advanced_sushi_args=False):
        run_choice = choice_prompt.get(message=TO_RUN_SELECTED_PROMPT, options=TEMP_QUEUE_OPTIONS["sub_run_add"], nl_before=False)
        match run_choice:
            case 1 if confirm_prompt.get():
                return _run_and_queue_all(use_advanced_sushi_args=use_advanced_sushi_args)
            case 2:
                selected_jobs = temp_queue.select_jobs(prompt_message=TO_RUN_SELECTED_PROMPT)
                if selected_jobs and confirm_prompt.get("Run selected jobs and add to main queue?", nl_after=True):
                    main_queue.add_jobs(selected_jobs, task)
                    temp_queue.run_jobs(selected_jobs, use_advanced_sushi_args=use_advanced_sushi_args)
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
                
    # No need to filter for each render for now
    available_options = [
        opt[:2]
        for opt in TEMP_QUEUE_OPTIONS["top"]
        if (opt[2]() if len(opt) > 2 else True)
    ]

    while True:
        _show_queue_items(temp_queue.contents, task)
        is_single_job = len(temp_queue.contents) == 1
        
        top_lvl_choice = choice_prompt.get(options=available_options)
        match top_lvl_choice:
            case 1 | 2:
                use_advanced_sushi_args = top_lvl_choice == 2
                fn = _run_and_queue_all if is_single_job else _handle_run_and_queue_multiple
                exit_loop = fn(use_advanced_sushi_args)
                if exit_loop:
                    return True
            case 3:
                exit_loop =_queue_without_running_all() if is_single_job else _handle_queue_without_running_multiple()
                if exit_loop:
                    return True
            case _:
                return False
