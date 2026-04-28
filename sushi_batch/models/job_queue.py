from os import path

from ..ui.prompts import checklist_dialog

from ..utils import utils
from ..utils import console_utils as cu
from ..utils import file_utils as fu
from ..ui.prompts import confirm_prompt
from ..services.job_stream_selection_service import JobStreamSelectionService
from ..persistence.queue_persistence import QueuePersistence

from . import settings
from .enums import Status
from ..utils import constants


class JobQueue:
    def __init__(self, contents=None, in_memory=False):
        self.contents = contents if contents is not None else []
        self.in_memory = in_memory
        self._persistence = (
            None
            if in_memory
            else QueuePersistence(path.join(settings.config.data_path, "queue_data.json"))
        )

    def save(self):
        """Save queue contents to JSON file."""
        if self.in_memory or self._persistence is None:
            return
        self._persistence.save(self.contents)

    def load(self):
        """Load queue contents from JSON file."""
        if self.in_memory or self._persistence is None:
            return
        self.contents = self._persistence.load()

    def _add_sync_jobs(self, jobs_to_add, task):
        """Add selected jobs to queue"""
        try:
            if not jobs_to_add:
                cu.print_error("No jobs to add to queue!")
                return

            if task in constants.VIDEO_TASKS:
                JobStreamSelectionService.set_video_sync_job_streams(jobs_to_add)

            self.contents.extend(jobs_to_add)
            self.save()
        except Exception as e:
            cu.print_error(f"Error adding jobs to queue: {e}")

    def add_jobs(self, jobs_to_add, task):
        return utils.interrupt_signal_handler(self._add_sync_jobs)(jobs_to_add, task)

    def _remove_sync_jobs(self, jobs_to_remove):
        """Remove selected jobs from queue"""
        job_ids_to_remove = {job.idx for job in jobs_to_remove}
        try:
            self.contents = [
                job
                for job in self.contents
                if job.idx not in job_ids_to_remove
            ]

            self._clean_generated_files(jobs_to_remove)
            self.save()
        except Exception as e:
            cu.print_error(f"Error removing jobs: {e}")

    def remove_jobs(self, jobs_to_remove):
        return utils.interrupt_signal_handler(self._remove_sync_jobs)(jobs_to_remove)

    def _clean_generated_files(self, job_list, confirm_deletion=True):
        """Delete files generated for the specified jobs.
        This includes intermediate subtitle files generated for syncing and resampling.
        """
        if any(job.sync_status == Status.COMPLETED for job in job_list):
            if confirm_deletion and not confirm_prompt.get("Delete generated files (excluding merged video files)?", destructive=True):
                return

            fu.clean_generated_files(job_list)

    def clear(self):
        self.remove_jobs(self.contents)

    def clear_completed_and_failed_jobs(self):
        """ Clear completed and failed jobs from queue """
        jobs_to_remove = [
            job
            for job in self.contents
            if job.sync_status != Status.PENDING
        ]

        if jobs_to_remove:
            self.remove_jobs(jobs_to_remove)
            cu.print_success("Completed and failed jobs removed from queue.")
        else:
            cu.print_error("No completed or failed jobs to remove!")

    def select_jobs(self, prompt_title="Job Selection", prompt_message="", filter_fn=None):
        """Select jobs from queue in a checkbox dialog and return objects.

        filter_fn receives each job and should return True when that job should
        be shown/selectable in the dialog.
        """
        options = [   
            (job.idx, f"Job {job.idx} - {path.basename(job.src_file)} -> {path.basename(job.dst_file)} [{job.sync_status.name}]") 
            for job 
            in self.contents
            if (True if filter_fn is None else filter_fn(job))
        ]

        choice = checklist_dialog.get(title=prompt_title, message=prompt_message, options=options)   
        if not choice:
            cu.print_error("No jobs selected!")
            return None

        selected_display = '\n'.join(j[1] for j in options if j[0] in choice)
        cu.print_warning(f"{cu.fore.LIGHTYELLOW_EX}Selected \n{cu.fore.LIGHTBLUE_EX}{selected_display}\n", wait=False)

        return [
            job 
            for job 
            in self.contents 
            if job.idx in choice and (True if filter_fn is None else filter_fn(job))
        ]
