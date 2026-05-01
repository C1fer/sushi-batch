from typing import Callable, Literal

from ...models import settings as s
from ...models.enums import QueueTheme, Status
from ...models.job_queue import JobQueue, JobQueueContents
from ...utils import console_utils as cu
from ...utils.constants import MenuItem, DynamicMenuItem
from ..prompts import input_prompt
from .queue_themes import QUEUE_RENDERERS

type QueueStatsKey = Literal["total", "pending", "completed", "failed"]

TO_RUN_SELECTED_PROMPT = "Select which jobs to run:"

main_queue: JobQueue = JobQueue(in_memory=False)

def show_continue_confirmation(jobs: JobQueueContents, is_removing: bool = False) -> None:
    """Show confirmation prompt after adding jobs to main queue."""
    count: int = len(jobs)
    job_count: str = "1 job" if count == 1 else f"{count} jobs"
    action: str = "removed from" if is_removing else "added to"
    input_prompt.get(f"{job_count} {action} main queue. Press Enter to continue... ", success=True, nl_before=True, allow_empty=True)

def show_queue_items(queue: JobQueueContents, is_main_queue: bool) -> None:
    """Display the current job queue in the selected theme. Theme is chosen from settings."""
    cu.clear_screen()
    title: str = "Job Queue" if is_main_queue else "Jobs"
    cu.print_header(f"{title}")
    
    current_theme: QueueTheme = s.config.general.get("queue_theme")
    renderer: Callable[[JobQueueContents, bool], None] = QUEUE_RENDERERS.get(current_theme)
    renderer(queue, is_main_queue)

def get_full_queue_stats(queue: JobQueueContents) -> dict[QueueStatsKey, int]:
    """Return summary statistics for a given queue."""
    return {
        "total": len(queue),
        "pending": sum(1 for job in queue if job.sync.status == Status.PENDING),
        "completed": sum(1 for job in queue if job.sync.status == Status.COMPLETED),
        "failed": sum(1 for job in queue if job.sync.status == Status.FAILED),
    }

def get_queue_stats_by_key(queue: JobQueueContents, key: QueueStatsKey) -> int:
    """Return the count of jobs in a queue based on the reqn key."""
    return sum(1 for job in queue if job.sync.status == key)


def get_visible_options(options: list[MenuItem | DynamicMenuItem], validations: dict[str, bool]) -> list[MenuItem]:
    """Return the visible options from the given options based on the validations."""
    visible_options: list[MenuItem] = []
    for opt in options:
        match opt:
            case (choice_id, label):
                visible_options.append((choice_id, label))
            case (choice_id, label, is_visible_fn):
                if is_visible_fn(validations):
                    visible_options.append((choice_id, label))
    return visible_options

