import json
from os import path

from sushi_batch.external.ffmpeg import FFmpeg
from sushi_batch.external.opusenc import XiphOpusEncoder
from ..ui.prompts import checklist_dialog, input_prompt

from ..utils import utils
from ..utils import console_utils as cu
from ..utils import file_utils as fu
from ..utils.json_utils import JobDecoder, JobEncoder
from ..ui.prompts import confirm_prompt
from ..external.mkv_merge import MKVMerge
from ..external.sub_sync import Sushi
from ..external.sub_resample import SubResampler

from . import settings
from .enums import Status, Task, JobSelection, AudioEncodeCodec, AudioEncoder
from ..services.job_stream_selection_service import JobStreamSelectionService


class JobQueue:
    def __init__(self, contents=[]):
        self.contents = contents
        self.file_path = path.join(settings.config.data_path, "queue_data.json")

    def save(self):
        """Save queue contents to JSON file"""
        with open(self.file_path, "w", encoding="utf-8") as data_file:
            json.dump(self.contents, data_file, cls=JobEncoder, indent=4)
        return 0

    def load(self):
        """Load queue contents from JSON file"""
        if path.exists(self.file_path):
            with open(self.file_path, "r", encoding="utf-8") as data_file:
                self.contents = json.load(data_file, cls=JobDecoder)

    def _add_sync_jobs(self, jobs_to_add, task):
        """Add selected jobs to queue"""
        try:
            if not jobs_to_add:
                cu.print_error("No jobs to add to queue!")
                return

            if task in (Task.VIDEO_SYNC_DIR, Task.VIDEO_SYNC_FIL):
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
    
    def run_jobs(self, jobs_to_run=[], use_advanced_sushi_args=False):
        """ Run jobs selected by user. Supports advanced Sushi arguments if enabled in settings. """
        def _run_sub_sync(job, completed_video_jobs):
            Sushi.run(job, use_advanced_args=use_advanced_sushi_args)
            self.save()    
            if job.sync_status == Status.COMPLETED and job.task in (Task.VIDEO_SYNC_DIR, Task.VIDEO_SYNC_FIL):
                completed_video_jobs.append(job)

        try:
            if not jobs_to_run:
                cu.print_error("\nNo pending jobs to run!") 
                return
           
            cu.print_subheader("Running synchronization jobs")           

            completed_video_jobs = []
            for job in jobs_to_run:
                utils.interrupt_signal_handler(_run_sub_sync)(job, completed_video_jobs)
            
            if settings.config.merge_workflow.get("merge_files_after_execution") and completed_video_jobs:
                if MKVMerge.is_installed:
                    self.merge_completed_video_jobs(JobSelection.SELECTED, completed_video_jobs)
                else:
                    cu.print_error("\nMKVMerge could not be found. Video files cannot be merged.")
                    
            input_prompt.get("All jobs have been processed. Press Enter to continue... ", success=True, nl_before=True, allow_empty=True)
        except Exception as e:
            cu.print_error(f"Error running jobs: {e}")

    def _resample_before_merge(self, job):
        """Resample subtitle file before merging. 
        Skipped if script and video resolutions match.
        """
        if not SubResampler.is_resample_needed(job):
            return False
        
        resample_done = SubResampler.run(job)
        if resample_done:
            cu.print_success(f"[Job {job.idx} - SubResampler] Resampling completed successfully.", nl_before=False, wait=False)
            return True
        else:
            cu.print_warning(f"[Job {job.idx} - SubResampler] Subtitle could not be resampled. Merging synced subtitle instead.", nl_before=False, wait=False)
            return False
        
    def _encode_to_opus(self, job):
        selected_encoder = settings.config.merge_workflow.get("encode_codec_settings", {}).get(AudioEncodeCodec.OPUS.name, None).get("encoder", None)
        if selected_encoder == AudioEncoder.XIPH_OPUSENC:
            if XiphOpusEncoder.is_available:
                return XiphOpusEncoder.encode(job)
            else:
                cu.print_warning(f"[Job {job.idx} - Opusenc] Opusenc could not be found. Attempting to encode with FFmpeg instead.", nl_before=False, wait=False)
        return FFmpeg.encode_lossless_audio(job)
        
    def _encode_audio_before_merge(self, job):
        """Encode audio file before merging if selected in settings. 
        Skipped if source audio codec is already compatible with selected codec or if no audio stream is found.
        """
        if not FFmpeg.is_audio_encode_needed(job):
            return None
        
        if settings.config.merge_workflow.get("encode_codec") == AudioEncodeCodec.OPUS:
                output_path = self._encode_to_opus(job)
        else: 
            output_path = FFmpeg.encode_lossless_audio(job) 
        
        if output_path:
            cu.print_success(f"[Job {job.idx} - FFmpeg] Audio Track encoded successfully.", nl_before=False, wait=False)
            return output_path
        else:
            cu.print_warning(f"[Job {job.idx} - FFmpeg] Audio could not be encoded. Merging original audio track instead.", nl_before=False, wait=False)
            return None
        
    def _clean_generated_files(self, job_list, confirm_deletion=True):
        """Delete files generated for the specified jobs.
        This includes intermediate subtitle files generated for syncing and resampling.
        """
        if any(job.sync_status == Status.COMPLETED for job in job_list):
            if confirm_deletion and not confirm_prompt.get("Delete generated files (excluding merged video files)?", destructive=True):
                return

            fu.clean_generated_files(job_list)
        
    def merge_completed_video_jobs(self, selection_type, selected_jobs=None):
        """ Generate a new video file from completed video tasks """
        def _run_merge(job, do_resample, do_encode_audio):
            encoded_audio_path = self._encode_audio_before_merge(job) if do_encode_audio else None
            use_resampled_sub = self._resample_before_merge(job) if do_resample else False
            MKVMerge.run(job, use_resampled_sub=use_resampled_sub, encoded_audio_path=encoded_audio_path)
            self.save()

        completed_jobs = [
            job for job in self.contents
            if job.sync_status == Status.COMPLETED 
            and job.task in (Task.VIDEO_SYNC_DIR, Task.VIDEO_SYNC_FIL)
            and not job.merged
        ]  if selection_type == JobSelection.ALL else selected_jobs

        if not completed_jobs:
            cu.print_error("No completed jobs to merge!")
            return

        cu.print_subheader("Merging files")
        
        do_audio_encode = settings.config.merge_workflow.get("encode_lossless_audio_before_merging")
        do_resample = True
        if settings.config.merge_workflow.get("resample_subs_on_merge") and not SubResampler.is_installed:
            do_resample = False
            cu.print_error("Aegisub-CLI could not be found. Subtitle resampling will be skipped.")

        for job in completed_jobs:
            utils.interrupt_signal_handler(_run_merge)(job, do_resample, do_audio_encode)

        if settings.config.merge_workflow.get("delete_generated_files_after_merge"):
            successfully_merged_jobs = [job for job in completed_jobs if job.merged]
            self._clean_generated_files(successfully_merged_jobs, confirm_deletion=False)

        input_prompt.get("Merging process completed. Press Enter to continue... ", success=True, allow_empty=True, nl_before=True)

    def _clear_queue(self, trigger_file_cleanup):
        """ Clear queue contents """
        if trigger_file_cleanup:
            self._clean_generated_files(self.contents.copy())

        self.contents.clear()
        self.save()

    def clear(self, trigger_file_cleanup=True):
        return utils.interrupt_signal_handler(self._clear_queue)(trigger_file_cleanup)

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
