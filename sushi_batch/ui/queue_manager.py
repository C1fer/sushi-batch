from typing import Callable, Literal, TypeAlias, cast

from ..external.mkv_merge import MKVMerge
from ..models import settings as s
from ..models.enums import QueueTheme, Status, Task
from ..models.job.video_sync_job import VideoSyncJob
from ..models.job_queue import JobQueue, JobQueueContents
from ..services.queue_execution_service import QueueExecutionService
from ..utils import console_utils as cu
from ..utils import utils
from .prompts import choice_prompt, confirm_prompt, input_prompt
from .queue_themes import QUEUE_RENDERERS

QueueStatsKey = Literal["total", "pending", "completed", "failed"]
ToolbarData: TypeAlias = list[tuple[str, str]] # tuple[style, text]

MenuItemValidator: TypeAlias = Callable[[dict[str, bool]], bool]
QueueMenuItems: TypeAlias = list[tuple[int, str] | tuple[int, str, MenuItemValidator]]

MAIN_QUEUE_TOP_OPTIONS: QueueMenuItems =  [
    (1, "Run Jobs",),
    (2, "Run Jobs (Include Advanced Sushi Args)", lambda args: args["enable_advanced_sushi_args"]),
    (3, "Remove Jobs"),
    (4, "Merge Completed Video Jobs", lambda args: args["can_merge"]),
    (5, "Go Back"),
]

MAIN_QUEUE_SUB_OPTIONS: dict[str, list[tuple[int, str]]] = {
    "run": [
        (1, "All Pending"),
        (2, "Selected"),
        (3, "Go Back"),
    ],
    "remove": [
        (1, "All"),
        (2, "Completed and Failed"),
        (3, "Selected"),
        (4, "Go Back"),
    ],
    "merge": [
        (1, "All Completed"),
        (2, "Selected"),
        (3, "Go Back"),
    ]
}

TEMP_QUEUE_TOP_OPTIONS: QueueMenuItems = [
    (1, "Run and Add to Main Queue"),
    (2, "Run and Add to Main Queue (Include Advanced Sushi Args)", lambda args: args["enable_advanced_sushi_args"]),
    (3, "Queue Without Running"),
    (4, "Return to Main Menu"),
]

TEMP_QUEUE_SUB_OPTIONS: dict[str, list[tuple[int, str]]] = {
    "run_add": [
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


def _show_continue_confirmation(jobs: JobQueueContents, is_removing: bool = False) -> None:
    """Show confirmation prompt after adding jobs to main queue."""
    count: int = len(jobs)
    job_count: str = "1 job" if count == 1 else f"{count} jobs"
    action: str = "removed from" if is_removing else "added to"
    input_prompt.get(f"{job_count} {action} main queue. Press Enter to continue... ", success=True, nl_before=True, allow_empty=True)

def _show_queue_items(queue: JobQueueContents, is_main_queue: bool) -> None:
    """Display the current job queue in the selected theme. Theme is chosen from settings."""
    cu.clear_screen()
    title: str = "Job Queue" if is_main_queue else "Jobs"
    cu.print_header(f"{title}")
    
    current_theme: QueueTheme = s.config.general.get("queue_theme")
    renderer: Callable[[JobQueueContents, bool], None] = QUEUE_RENDERERS.get(current_theme)
    renderer(queue, is_main_queue)

def get_full_queue_stats(queue: JobQueueContents) -> dict[QueueStatsKey, int]:
    """Return summary statistics for the job queue, including total jobs, pending, completed, and failed counts."""
    return {
        "total": len(queue),
        "pending": sum(1 for job in queue if job.sync.status == Status.PENDING),
        "completed": sum(1 for job in queue if job.sync.status == Status.COMPLETED),
        "failed": sum(1 for job in queue if job.sync.status == Status.FAILED),
    }

def get_queue_stats_by_key(queue: JobQueueContents, key: QueueStatsKey) -> int:
    """Return the count of jobs in the queue for the given key."""
    return sum(1 for job in queue if job.sync.status == key)

def get_stats_bar(queue: JobQueueContents) -> tuple[ToolbarData, int]:
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

def get_visible_options(options: QueueMenuItems, validations: dict[str, bool]) -> list[tuple[int, str]]:
    """Return the visible options from the given options based on the validations."""
    visible_options: list[tuple[int, str]] = []
    for opt in options:
        match opt:
            case (choice_id, label):
                visible_options.append((choice_id, label))
            case (choice_id, label, is_visible_fn):
                if is_visible_fn(validations):
                    visible_options.append((choice_id, label))
    return visible_options

def show_main_queue() -> None:
    """Display the main job queue and handle user interactions."""
    def _handle_run_options(toolbar_stats: ToolbarData, pending_count: int, use_advanced_sushi_args: bool = False) -> None:
        if pending_count == 0:
            cu.print_warning("No pending jobs to run.")
            return

        run_choice: int = choice_prompt.get(message=TO_RUN_SELECTED_PROMPT, options=MAIN_QUEUE_SUB_OPTIONS["run"], nl_before=False, bottom_toolbar=toolbar_stats)
        match run_choice:
            case 1 if confirm_prompt.get(bottom_toolbar=toolbar_stats):
                selected_jobs: JobQueueContents = [job for job in main_queue.contents if job.sync.status == Status.PENDING]
                QueueExecutionService.run_jobs(selected_jobs, use_advanced_sushi_args=use_advanced_sushi_args, parent_queue=main_queue)
            case 2:
                selected_jobs: JobQueueContents = main_queue.select_jobs(
                    prompt_message=TO_RUN_SELECTED_PROMPT,
                    filter_fn=lambda j: j.sync.status == Status.PENDING,
                )
                if selected_jobs and confirm_prompt.get("Run selected jobs?", bottom_toolbar=toolbar_stats):
                    QueueExecutionService.run_jobs(selected_jobs, use_advanced_sushi_args=use_advanced_sushi_args, parent_queue=main_queue)

    def _handle_remove_options(toolbar_stats: ToolbarData) -> None:
        remove_choice = choice_prompt.get(message=TO_REMOVE_SELECTED_PROMPT, options=MAIN_QUEUE_SUB_OPTIONS["remove"], nl_before=False, bottom_toolbar=toolbar_stats)
        match remove_choice:
            case 1 if confirm_prompt.get("Clear job queue?", destructive=True, bottom_toolbar=toolbar_stats):
                main_queue.clear()
                cu.print_success("All jobs removed from queue.")
            case 2 if confirm_prompt.get(destructive=True, bottom_toolbar=toolbar_stats):
                main_queue.clear_completed_and_failed_jobs()
            case 3:
                selected_jobs: JobQueueContents = main_queue.select_jobs(prompt_message=TO_REMOVE_SELECTED_PROMPT)
                if selected_jobs and confirm_prompt.get("Remove selected jobs from queue?", destructive=True, bottom_toolbar=toolbar_stats):
                    main_queue.remove_jobs(selected_jobs)
                    _show_continue_confirmation(selected_jobs, is_removing=True)

    def _handle_merge_options(toolbar_stats: ToolbarData) -> None:
        if not MKVMerge.is_installed:
            cu.print_error("MKVMerge could not be found! Install MKVMerge to enable merging functionality.", nl_before=True)
            return
        
        merge_choice: int = choice_prompt.get(message=TO_MERGE_SELECTED_PROMPT, options=MAIN_QUEUE_SUB_OPTIONS["merge"], nl_before=False, bottom_toolbar=toolbar_stats)
        match merge_choice:
            case 1:
                selected_jobs: list[VideoSyncJob] = [
                    job
                    for job in main_queue.contents
                    if job.sync.status == Status.COMPLETED
                    and isinstance(job, VideoSyncJob)
                    and not job.merge.done
                ]
                if confirm_prompt.get(bottom_toolbar=toolbar_stats):
                    QueueExecutionService.merge_completed_video_jobs(selected_jobs, parent_queue=main_queue)
            case 2:
                selected_jobs = cast(list[VideoSyncJob], main_queue.select_jobs(
                    prompt_message=TO_MERGE_SELECTED_PROMPT,
                    filter_fn=lambda j: (
                        j.sync.status == Status.COMPLETED
                        and isinstance(j, VideoSyncJob)
                        and not j.merge.done
                    ),
                ))
                if selected_jobs and confirm_prompt.get("Merge selected jobs?", bottom_toolbar=toolbar_stats):
                    QueueExecutionService.merge_completed_video_jobs(selected_jobs, parent_queue=main_queue)
    
    while True:
        _show_queue_items(main_queue.contents, is_main_queue=True)
        bottom_toolbar, pending_count = get_stats_bar(main_queue.contents)

        validations: dict[str, bool] = {
            "enable_advanced_sushi_args": bool(s.config.sync_workflow.get("enable_sushi_advanced_args")),
            "can_merge": bool(
                MKVMerge.is_installed
                and any(
                    j
                    for j in main_queue.contents
                    if j.sync.status == Status.COMPLETED
                    and isinstance(j, VideoSyncJob)
                    and not j.merge.done
                )
            ),
        }

        visible_options: list[tuple[int, str]] = get_visible_options(MAIN_QUEUE_TOP_OPTIONS, validations)

        top_lvl_choice: int = choice_prompt.get(options=visible_options, bottom_toolbar=bottom_toolbar)
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

def _show_temp_queue(temp_queue: JobQueue, task: Task) -> bool:
    """Handle options for the temporary job queue created after file selection."""
    def _run_and_queue_all(use_advanced_sushi_args: bool= False) -> bool:
        current_queue_length: int = len(main_queue.contents)
        main_queue.add_jobs(temp_queue.contents, task)
        to_run: JobQueueContents = main_queue.contents[current_queue_length:] # Run the new jobs that were added to the main queue
        QueueExecutionService.run_jobs(to_run, use_advanced_sushi_args=use_advanced_sushi_args, parent_queue=main_queue)
        return True

    def _queue_without_running_all() -> bool:
        main_queue.add_jobs(temp_queue.contents, task)
        _show_continue_confirmation(temp_queue.contents)
        return True

    def _handle_run_and_queue_multiple(use_advanced_sushi_args: bool = False) -> bool:
        run_choice: int = choice_prompt.get(message=TO_RUN_SELECTED_PROMPT, options=TEMP_QUEUE_SUB_OPTIONS["run_add"], nl_before=False)
        match run_choice:
            case 1 if confirm_prompt.get():
                return _run_and_queue_all(use_advanced_sushi_args=use_advanced_sushi_args)
            case 2:
                selected_jobs: JobQueueContents = temp_queue.select_jobs(prompt_message=TO_RUN_SELECTED_PROMPT)
                if selected_jobs and confirm_prompt.get("Run selected jobs and add to main queue?", nl_after=True):
                    main_queue.add_jobs(selected_jobs, task)
                    QueueExecutionService.run_jobs(selected_jobs, use_advanced_sushi_args=use_advanced_sushi_args)
                    return True
        return False

    def _handle_queue_without_running_multiple() -> bool:
        add_choice: int = choice_prompt.get(message=TO_ADD_SELECTED_PROMPT, options=TEMP_QUEUE_SUB_OPTIONS["run_add"], nl_before=False)
        match add_choice:
            case 1:
                return _queue_without_running_all()
            case 2:
                selected_jobs: JobQueueContents = temp_queue.select_jobs(prompt_message=TO_ADD_SELECTED_PROMPT)
                if selected_jobs and confirm_prompt.get("Add selected jobs to main queue?", nl_after=True):
                    main_queue.add_jobs(selected_jobs, task)
                    _show_continue_confirmation(selected_jobs)
                    return True
        return False
        
    validations: dict[str, bool] = { "enable_advanced_sushi_args": bool(s.config.sync_workflow.get("enable_sushi_advanced_args")) }
    visible_options: list[tuple[int, str]] = get_visible_options(TEMP_QUEUE_TOP_OPTIONS, validations)

    while True:
        _show_queue_items(temp_queue.contents, is_main_queue=False)
        is_single_job: bool = len(temp_queue.contents) == 1
        
        top_lvl_choice: int = choice_prompt.get(options=visible_options, nl_before=True)
        match top_lvl_choice:
            case 1 | 2:
                use_advanced_sushi_args: bool = top_lvl_choice == 2
                exit_loop: bool = _run_and_queue_all(use_advanced_sushi_args=use_advanced_sushi_args) if is_single_job else _handle_run_and_queue_multiple(use_advanced_sushi_args=use_advanced_sushi_args)
                if exit_loop:
                    return True
            case 3:
                exit_loop =_queue_without_running_all() if is_single_job else _handle_queue_without_running_multiple()
                if exit_loop:
                    return True
            case _:
                return False

def show_temp_queue(temp_queue: JobQueue, task: Task) -> None:
    return utils.interrupt_signal_handler(_show_temp_queue)(temp_queue, task)