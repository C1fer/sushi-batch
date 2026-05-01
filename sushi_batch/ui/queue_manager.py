from typing import Literal

from ..external.mkv_merge import MKVMerge
from ..models import settings as s
from ..models.enums import Status, Task
from ..models.job.audio_sync_job import AudioSyncJob
from ..models.job.video_sync_job import VideoSyncJob
from ..models.job_queue import JobQueue
from ..services.queue_execution_service import QueueExecutionService
from ..utils import console_utils as cu
from ..utils import utils
from .prompts import choice_prompt, confirm_prompt, input_prompt
from .queue_themes import QUEUE_RENDERERS

QueueStatsKey = Literal["total", "pending", "completed", "failed"]

MAIN_QUEUE_OPTIONS= {
    "top": [
        (1, "Run Jobs"),
        (2, "Run Jobs (Include Advanced Sushi Args)", lambda q: s.config.sync_workflow.get("enable_sushi_advanced_args")),
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
        (2, "Run and Add to Main Queue (Include Advanced Sushi Args)", lambda: s.config.sync_workflow.get("enable_sushi_advanced_args")),
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

main_queue = JobQueue(in_memory=False)

def _show_continue_confirmation(jobs, is_removing=False):
    """Show confirmation prompt after adding jobs to main queue."""
    count = len(jobs)
    job_count = "1 job" if count == 1 else f"{count} jobs"
    action = "removed from" if is_removing else "added to"
    input_prompt.get(f"{job_count} {action} main queue. Press Enter to continue... ", success=True, nl_before=True, allow_empty=True)

def _show_queue_items(queue: list[AudioSyncJob | VideoSyncJob], current_task: Task) -> None:
    """Display the current job queue in the selected theme. Theme is chosen from settings."""
    cu.clear_screen()
    title = "Job Queue" if current_task == Task.JOB_QUEUE else "Jobs"
    cu.print_header(f"{title}")
    
    current_theme = s.config.general.get("queue_theme")
    renderer = QUEUE_RENDERERS.get(current_theme, lambda q, t: cu.print_error("Invalid queue theme selected."))
    renderer(queue, current_task)


def get_full_queue_stats(queue: list[AudioSyncJob | VideoSyncJob]) -> dict[QueueStatsKey, int]:
    """Return summary statistics for the job queue, including total jobs, pending, completed, and failed counts."""
    return {
        "total": len(queue),
        "pending": sum(1 for job in queue if job.sync.status == Status.PENDING),
        "completed": sum(1 for job in queue if job.sync.status == Status.COMPLETED),
        "failed": sum(1 for job in queue if job.sync.status == Status.FAILED),
    }

def get_queue_stats_by_key(queue: list[AudioSyncJob | VideoSyncJob], key: QueueStatsKey) -> int:
    """Return the count of jobs in the queue for the given key."""
    return sum(1 for job in queue if job.sync.status == key)

def get_stats_bar(queue: list[AudioSyncJob | VideoSyncJob]) -> tuple[list[tuple[str, str]], int]:
    """Generate a formatted status bar with per-field colors."""
    stats = get_full_queue_stats(queue)
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

def show_main_queue(task: Task) -> None:
    """Display the main job queue and handle user interactions."""
    def _handle_run_options(toolbar_stats: list[tuple[str, str]], pending_count: int, use_advanced_sushi_args: bool = False) -> None:
        if pending_count == 0:
            cu.print_warning("No pending jobs to run.")
            return

        run_choice = choice_prompt.get(message=TO_RUN_SELECTED_PROMPT, options=MAIN_QUEUE_OPTIONS["sub_run"], nl_before=False, bottom_toolbar=toolbar_stats)
        match run_choice:
            case 1 if confirm_prompt.get(bottom_toolbar=toolbar_stats):
                selected_jobs = [job for job in main_queue.contents if job.sync.status == Status.PENDING]
                QueueExecutionService.run_jobs(selected_jobs, use_advanced_sushi_args=use_advanced_sushi_args, parent_queue=main_queue)
            case 2:
                selected_jobs = main_queue.select_jobs(
                    prompt_message=TO_RUN_SELECTED_PROMPT,
                    filter_fn=lambda j: j.sync.status == Status.PENDING,
                )
                if selected_jobs and confirm_prompt.get("Run selected jobs?", bottom_toolbar=toolbar_stats):
                    QueueExecutionService.run_jobs(selected_jobs, use_advanced_sushi_args=use_advanced_sushi_args, parent_queue=main_queue)

    def _handle_remove_options(toolbar_stats: list[tuple[str, str]]):
        remove_choice = choice_prompt.get(message=TO_REMOVE_SELECTED_PROMPT, options=MAIN_QUEUE_OPTIONS["sub_remove"], nl_before=False, bottom_toolbar=toolbar_stats)
        match remove_choice:
            case 1 if confirm_prompt.get("Clear job queue?", destructive=True, bottom_toolbar=toolbar_stats):
                main_queue.clear()
                cu.print_success("All jobs removed from queue.")
            case 2 if confirm_prompt.get(destructive=True, bottom_toolbar=toolbar_stats):
                main_queue.clear_completed_and_failed_jobs()
            case 3:
                selected_jobs = main_queue.select_jobs(prompt_message=TO_REMOVE_SELECTED_PROMPT)
                if selected_jobs and confirm_prompt.get("Remove selected jobs from queue?", destructive=True, bottom_toolbar=toolbar_stats):
                    main_queue.remove_jobs(selected_jobs)
                    _show_continue_confirmation(selected_jobs, is_removing=True)

    def _handle_merge_options(toolbar_stats: list[tuple[str, str]]):
        if not  MKVMerge.is_installed:
            cu.print_error("MKVMerge could not be found! Install MKVMerge to enable merging functionality.", nl_before=True)
            return
        
        merge_choice = choice_prompt.get(message=TO_MERGE_SELECTED_PROMPT, options=MAIN_QUEUE_OPTIONS["sub_merge"], nl_before=False, bottom_toolbar=toolbar_stats)
        match merge_choice:
            case 1:
                selected_jobs = [
                    job
                    for job in main_queue.contents
                    if job.sync.status == Status.COMPLETED
                    and isinstance(job, VideoSyncJob)
                    and not job.merge.done
                ]
                if confirm_prompt.get(bottom_toolbar=toolbar_stats):
                    QueueExecutionService.merge_completed_video_jobs(selected_jobs, parent_queue=main_queue)
            case 2:
                selected_jobs = main_queue.select_jobs(
                    prompt_message=TO_MERGE_SELECTED_PROMPT,
                    filter_fn=lambda j: (
                        j.sync.status == Status.COMPLETED
                        and isinstance(j, VideoSyncJob)
                        and not j.merge.done
                    ),
                )
                if selected_jobs and confirm_prompt.get("Merge selected jobs?", bottom_toolbar=toolbar_stats):
                    QueueExecutionService.merge_completed_video_jobs(selected_jobs, parent_queue=main_queue)
    
    while True:
        _show_queue_items(main_queue.contents, task)
        bottom_toolbar, pending_count = get_stats_bar()

        validations = {
            "to_merge": any(j for j in main_queue.contents if j.sync.status == Status.COMPLETED and isinstance(j, VideoSyncJob) and not j.merge.done)
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


def _show_temp_queue(temp_queue: JobQueue, task: Task) -> None:
    """Handle options for the temporary job queue created after file selection."""
    def _run_and_queue_all(use_advanced_sushi_args: bool= False) -> bool:
        current_queue_length = len(main_queue.contents)
        main_queue.add_jobs(temp_queue.contents, task)
        to_run = main_queue.contents[current_queue_length:] # Run the new jobs that were added to the main queue
        QueueExecutionService.run_jobs(to_run, use_advanced_sushi_args=use_advanced_sushi_args, parent_queue=main_queue)
        return True

    def _queue_without_running_all() -> bool:
        main_queue.add_jobs(temp_queue.contents, task)
        _show_continue_confirmation(temp_queue.contents)
        return True

    def _handle_run_and_queue_multiple(use_advanced_sushi_args: bool = False) -> bool:
        run_choice = choice_prompt.get(message=TO_RUN_SELECTED_PROMPT, options=TEMP_QUEUE_OPTIONS["sub_run_add"], nl_before=False)
        match run_choice:
            case 1 if confirm_prompt.get():
                return _run_and_queue_all(use_advanced_sushi_args=use_advanced_sushi_args)
            case 2:
                selected_jobs = temp_queue.select_jobs(prompt_message=TO_RUN_SELECTED_PROMPT)
                if selected_jobs and confirm_prompt.get("Run selected jobs and add to main queue?", nl_after=True):
                    main_queue.add_jobs(selected_jobs, task)
                    QueueExecutionService.run_jobs(selected_jobs, use_advanced_sushi_args=use_advanced_sushi_args)
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
                
    available_options = [
        opt[:2]
        for opt in TEMP_QUEUE_OPTIONS["top"]
        if (opt[2]() if len(opt) > 2 else True)
    ]

    while True:
        _show_queue_items(temp_queue.contents, task)
        is_single_job = len(temp_queue.contents) == 1
        
        top_lvl_choice = choice_prompt.get(options=available_options, nl_before=True)
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
                return

def show_temp_queue(temp_queue: JobQueue, task: Task) -> None:
    return utils.interrupt_signal_handler(_show_temp_queue)(temp_queue, task)