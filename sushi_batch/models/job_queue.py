from typing import Callable, cast
from pathlib import Path

from ..ui.prompts import checklist_dialog

from ..utils import utils
from ..utils import console_utils as cu
from ..utils import file_utils as fu
from ..ui.prompts import confirm_prompt
from ..services.job_stream_selection_service import JobStreamSelectionService
from ..persistence.queue_persistence import QueuePersistence

from . import settings
from .enums import Status, Task
from ..utils import constants
from ..models.job.audio_sync_job import AudioSyncJob
from ..models.job.video_sync_job import VideoSyncJob

type JobQueueContents = list[AudioSyncJob | VideoSyncJob]
type JobFilterFn = Callable[[AudioSyncJob | VideoSyncJob], bool]

class JobQueue:
    def __init__(self, contents: JobQueueContents | None = None, in_memory: bool = False):
        self.contents: JobQueueContents = contents if contents is not None else []
        self.in_memory: bool = in_memory
        self._persistence: QueuePersistence | None = (
            None
            if in_memory
            else QueuePersistence(Path(settings.config.data_path) / "queue_data.json")
        )

    def save(self) -> None:
        """Save queue contents to JSON file."""
        if self.in_memory or self._persistence is None:
            return
        self._persistence.save(self.contents)

    def load(self) -> None:
        """Load queue contents from JSON file."""
        if self.in_memory or self._persistence is None:
            self.contents = []
            return
        self.contents = [
            AudioSyncJob.from_dct(dct)
            if dct.get("sync").get("task") in (Task.AUDIO_SYNC_DIR.name, Task.AUDIO_SYNC_FIL.name)
            else VideoSyncJob.from_dct(dct)
            for dct in self._persistence.load()
        ]

    def _add_sync_jobs(self, jobs_to_add: JobQueueContents, task: Task) -> None:
        """Add selected jobs to queue"""
        try:
            if not jobs_to_add:
                cu.print_error("No jobs to add to queue!")
                return

            if task in constants.VIDEO_TASKS:
                JobStreamSelectionService.set_video_sync_job_streams(cast(list[VideoSyncJob], jobs_to_add))

            self.contents.extend(jobs_to_add)
            self.save()
        except Exception as e:
            cu.print_error(f"Error adding jobs to queue: {e}")

    def add_jobs(self, jobs_to_add: JobQueueContents, task: Task) -> None:
        return utils.interrupt_signal_handler(self._add_sync_jobs)(jobs_to_add, task)

    def _remove_sync_jobs(self, jobs_to_remove: JobQueueContents) -> None:
        """Remove selected jobs from queue"""
        job_ids_to_remove: set[int] = {job.id for job in jobs_to_remove}
        try:
            self.contents = [
                job
                for job in self.contents
                if job.id not in job_ids_to_remove
            ]

            self.clean_generated_files(jobs_to_remove)
            self.save()
        except Exception as e:
            cu.print_error(f"Error removing jobs: {e}")

    def remove_jobs(self, jobs_to_remove: JobQueueContents) -> None:
        return utils.interrupt_signal_handler(self._remove_sync_jobs)(jobs_to_remove)

    def clean_generated_files(self, job_list: JobQueueContents, confirm_deletion: bool = True) -> None:
        """Delete files generated for the specified jobs.
        This includes intermediate subtitle files generated for syncing and resampling.
        """
        if any(job.sync.status == Status.COMPLETED for job in job_list if isinstance(job, VideoSyncJob)):
            if confirm_deletion and not confirm_prompt.get("Delete generated files (excluding merged video files)?", destructive=True):
                return

            fu.clean_generated_files(job_list)

    def clear(self) -> None:
        self.remove_jobs(self.contents)

    def clear_completed_and_failed_jobs(self) -> None:
        """ Clear completed and failed jobs from queue """
        jobs_to_remove = [
            job
            for job in self.contents
            if job.sync.status != Status.PENDING
        ]

        if jobs_to_remove:
            self.remove_jobs(jobs_to_remove)
            cu.print_success("Completed and failed jobs removed from queue.")
        else:
            cu.print_error("No completed or failed jobs to remove!")

    def select_jobs(self, prompt_title: str = "Job Selection", prompt_message: str = "", filter_fn: JobFilterFn | None = None) -> JobQueueContents:
        """Select jobs from queue in a checkbox dialog and return objects.

        filter_fn receives each job and should return True when that job should
        be shown/selectable in the dialog.
        """
        options = [   
            (job.id, f"Job {job.id} - {Path(job.src_filepath).name} -> {Path(job.dst_filepath).name} [{job.sync.status.name}]") 
            for job 
            in self.contents
            if (True if filter_fn is None else filter_fn(job))
        ]

        choice = checklist_dialog.get(title=prompt_title, message=prompt_message, options=options)   
        if not choice:
            cu.print_error("No jobs selected!")
            return []

        selected_display = '\n'.join(j[1] for j in options if j[0] in choice)
        cu.print_warning(f"{cu.fore.LIGHTYELLOW_EX}Selected \n{cu.fore.LIGHTBLUE_EX}{selected_display}\n", wait=False)

        return [
            job 
            for job 
            in self.contents 
            if job.id in choice and (True if filter_fn is None else filter_fn(job))
        ]
