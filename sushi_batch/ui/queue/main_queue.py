from typing import cast

from ...external.mkv_merge import MKVMerge
from ...models import settings as s
from ...models.enums import Status
from ...models.job.video_sync_job import VideoSyncJob
from ...models.job_queue import JobQueueContents
from ...services.queue_execution_service import QueueExecutionService
from ...utils import console_utils as cu
from ...utils.constants import MenuItem, ToolbarData, DynamicMenuItem
from ..prompts import choice_prompt, confirm_prompt
from . import queue_manager as qm


MENU_OPTIONS: list[MenuItem | DynamicMenuItem] = [
    (1, "Run Jobs",),
    (2, "Run Jobs (Include Advanced Sushi Args)", lambda args: args["enable_advanced_sushi_args"]),
    (3, "Remove Jobs"),
    (4, "Merge Completed Video Jobs", lambda args: args["can_merge"]),
    (5, "Go Back"),
]

MENU_SUB_OPTIONS: dict[str, list[MenuItem]] = {
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

TO_REMOVE_SELECTED_PROMPT: str = "Select which jobs to remove from queue:"
TO_MERGE_SELECTED_PROMPT: str = "Select which video jobs to merge:"


def _get_stats_bar(queue: JobQueueContents) -> tuple[ToolbarData, int]:
    """Generate a formatted status bar with per-field colors."""
    stats: dict[qm.QueueStatsKey, int] = qm.get_full_queue_stats(queue)
    separator_classname = ("class:bottom-toolbar.sep", " | ")
    bar: ToolbarData = [
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

def _handle_run_options(toolbar_stats: ToolbarData, pending_count: int, use_advanced_sushi_args: bool = False) -> None:
    """Handle 'Run Jobs' submenu options."""
    if pending_count == 0:
        cu.print_warning("No pending jobs to run.")
        return

    run_choice: int = choice_prompt.get(message=qm.TO_RUN_SELECTED_PROMPT, options=MENU_SUB_OPTIONS["run"], nl_before=False, bottom_toolbar=toolbar_stats)
    match run_choice:
        case 1 if confirm_prompt.get(bottom_toolbar=toolbar_stats):
            selected_jobs: JobQueueContents = [job for job in qm.main_queue.contents if job.sync.status == Status.PENDING]
            QueueExecutionService.run_jobs(selected_jobs, use_advanced_sushi_args=use_advanced_sushi_args, parent_queue=main_queue)
        case 2:
            selected_jobs: JobQueueContents = qm.main_queue.select_jobs(
                prompt_message=qm.TO_RUN_SELECTED_PROMPT,
                filter_fn=lambda j: j.sync.status == Status.PENDING,
            )
            if selected_jobs and confirm_prompt.get("Run selected jobs?", bottom_toolbar=toolbar_stats):
                QueueExecutionService.run_jobs(selected_jobs, use_advanced_sushi_args=use_advanced_sushi_args, parent_queue=main_queue)

def _handle_remove_options(toolbar_stats: ToolbarData) -> None:
    """Handle 'Remove Jobs' submenu options."""
    remove_choice: int = choice_prompt.get(message=TO_REMOVE_SELECTED_PROMPT, options=MENU_SUB_OPTIONS["remove"], nl_before=False, bottom_toolbar=toolbar_stats)
    match remove_choice:
        case 1 if confirm_prompt.get("Clear job queue?", destructive=True, bottom_toolbar=toolbar_stats):
            qm.main_queue.clear()
            cu.print_success("All jobs removed from queue.")
        case 2 if confirm_prompt.get(destructive=True, bottom_toolbar=toolbar_stats):
            qm.main_queue.clear_completed_and_failed_jobs()
        case 3:
            selected_jobs: JobQueueContents = qm.main_queue.select_jobs(prompt_message=TO_REMOVE_SELECTED_PROMPT)
            if selected_jobs and confirm_prompt.get("Remove selected jobs from queue?", destructive=True, bottom_toolbar=toolbar_stats):
                qm.main_queue.remove_jobs(selected_jobs)
                qm.show_continue_confirmation(selected_jobs, is_removing=True)

def _handle_merge_options(toolbar_stats: ToolbarData) -> None:
    """Handle 'Merge Completed Video Jobs' submenu options."""
    if not MKVMerge.is_installed:
        cu.print_error("MKVMerge could not be found! Install MKVMerge to enable merging functionality.", nl_before=True)
        return
        
    merge_choice: int = choice_prompt.get(message=TO_MERGE_SELECTED_PROMPT, options=MENU_SUB_OPTIONS["merge"], nl_before=False, bottom_toolbar=toolbar_stats)
    match merge_choice:
        case 1:
            selected_jobs: list[VideoSyncJob] = [
                job
                for job in qm.main_queue.contents
                if job.sync.status == Status.COMPLETED
                and isinstance(job, VideoSyncJob)
                and not job.merge.done
            ]
            if confirm_prompt.get(bottom_toolbar=toolbar_stats):
                QueueExecutionService.merge_completed_video_jobs(selected_jobs, parent_queue=main_queue)
        case 2:
            selected_jobs = cast(list[VideoSyncJob], qm.main_queue.select_jobs(
                prompt_message=TO_MERGE_SELECTED_PROMPT,
                filter_fn=lambda j: (
                    j.sync.status == Status.COMPLETED
                    and isinstance(j, VideoSyncJob)
                    and not j.merge.done
                ),
            ))
            if selected_jobs and confirm_prompt.get("Merge selected jobs?", bottom_toolbar=toolbar_stats):
                QueueExecutionService.merge_completed_video_jobs(selected_jobs, parent_queue=main_queue)

def show_main_queue() -> None:
    """Display the main job queue and handle user interactions."""
    while True:
        qm.show_queue_items(qm.main_queue.contents, is_main_queue=True)
        bottom_toolbar, pending_count = _get_stats_bar(qm.main_queue.contents)

        validations: dict[str, bool] = {
            "enable_advanced_sushi_args": bool(s.config.sync_workflow.get("enable_sushi_advanced_args")),
            "can_merge": bool(
                MKVMerge.is_installed
                and any(
                    j
                    for j in qm.main_queue.contents
                    if j.sync.status == Status.COMPLETED
                    and isinstance(j, VideoSyncJob)
                    and not j.merge.done
                )
            ),
        }

        visible_options: list[MenuItem] = cu.get_visible_options(MENU_OPTIONS, validations)

        top_lvl_choice: int = choice_prompt.get(options=visible_options, bottom_toolbar=bottom_toolbar)
        match top_lvl_choice:
            case 1 | 2:
                _handle_run_options(toolbar_stats=bottom_toolbar, pending_count=pending_count, use_advanced_sushi_args=top_lvl_choice == 2)
            case 3:
                _handle_remove_options(toolbar_stats=bottom_toolbar)
                if not qm.main_queue.contents:
                    break
            case 4:
                _handle_merge_options(toolbar_stats=bottom_toolbar)
            case _:
                break