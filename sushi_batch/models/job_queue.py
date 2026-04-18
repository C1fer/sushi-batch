import json
from os import path

from sushi_batch.external.ffmpeg import FFmpeg

from ..utils import console_utils as cu
from ..utils import file_utils as fu
from ..utils.json_utils import JobDecoder, JobEncoder
from ..utils.prompts import choice_prompt, checklist_dialog, confirm_prompt
from ..external.mkv_merge import MKVMerge
from ..external.sub_sync import Sushi
from ..external.sub_resample import SubResampler

from . import settings
from .streams import Stream
from .enums import Status, Task, JobSelection


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

    def add_jobs(self, jobs_to_add, task):
        """Add selected jobs to queue"""
        try:
            if not jobs_to_add:
                cu.print_error("No jobs to add to queue!")
                return

            if task in (Task.VIDEO_SYNC_DIR, Task.VIDEO_SYNC_FIL):
                self._set_video_job_indexes(jobs_to_add)

            self.contents.extend(jobs_to_add)
            self.save()
        except Exception as e:
            cu.print_error(f"Error adding jobs to queue: {e}")

    def _set_video_job_indexes(self, jobs_to_queue):
        """Set audio and subtitle track indexes for video sync jobs"""
        if confirm_prompt.get("Select source/target tracks manually?"):
            self._set_stream_indexes(jobs_to_queue)
        else:
            for job in jobs_to_queue:
                indexes = self._get_stream_indexes(job, False)
                job.__dict__.update(indexes)

    def remove_jobs(self, jobs_to_remove):
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

    def run_jobs(self, jobs_to_run=[]):
        """ Run jobs selected by user"""
        try:
            if not jobs_to_run:
                cu.print_error("\nNo pending jobs to run!") 
                return

            cu.print_subheader("Executing synchronization jobs")           
            for job in jobs_to_run:
                Sushi.run(job)
                self.save()

            contains_video_tasks = any(
                job.task in (Task.VIDEO_SYNC_DIR, Task.VIDEO_SYNC_FIL)
                for job in jobs_to_run
            )

            if settings.config.merge_files_after_execution and contains_video_tasks:
                if MKVMerge.is_installed:
                    self.merge_completed_video_tasks(jobs_to_run)
                else:
                    cu.print_error("\nMKVMerge could not be found. Video files cannot be merged.")
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
        
    def _clean_generated_files(self, job_list, confirm_deletion=True):
        """Delete files generated for the specified jobs.
        This includes intermediate subtitle files generated for syncing and resampling.
        """
        if any(job.sync_status == Status.COMPLETED for job in job_list):
            if confirm_deletion and not confirm_prompt.get("Delete generated subtitle files?"):
                return

            fu.clean_generated_files(job_list)
        
    def merge_completed_video_jobs(self, selection_type, selected_jobs=None):
        """ Generate a new video file from completed video tasks """
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
        
        do_resample = True
        if settings.config.resample_subs_on_merge and not SubResampler.is_installed:
            do_resample = False
            cu.print_error("Aegisub-CLI could not be found. Subtitle resampling will be skipped.")

        for job in completed_jobs:
            use_resampled_sub = False
            if do_resample:
                use_resampled_sub = self._resample_before_merge(job)
                pass
            MKVMerge.run(job, use_resampled_sub=use_resampled_sub)
            self.save()

        if settings.config.delete_generated_files_after_merge:
            successfully_merged_jobs = [job for job in completed_jobs if job.merged]
            self._clean_generated_files(successfully_merged_jobs, confirm_deletion=False)

        input("\nPress Enter to go back... ")

    def clear(self, trigger_file_cleanup=True):
        """ Clear queue contents """
        if trigger_file_cleanup:
            self._clean_generated_files(self.contents.copy())

        self.contents.clear()
        self.save()

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

    def _get_stream_choice(self, streams, prompt, isTarget):
        """"Get user-selected stream from list"""
        if len(streams) == 1:
            print(prompt)
            _stream_color = cu.fore.YELLOW if isTarget else cu.fore.LIGHTBLUE_EX
            _stream_label = f"{_stream_color}{streams[0].display_name}"
            cu.print_warning(f"{cu.fore.LIGHTBLACK_EX}Only 1 stream available. Automatically selected: {_stream_label}", wait=False)
            return streams[0]

        options = [(int(stream.id), stream.display_name) for stream in streams]
       
        selected_stream_id = choice_prompt.get(prompt, options)
        return next(stream for stream in streams if int(stream.id) == selected_stream_id)

    def _show_stream_select_header(self, job):
        src_label = f"{cu.fore.LIGHTBLUE_EX}{path.basename(job.src_file)}"
        dst_label = f"{cu.fore.YELLOW}{path.basename(job.dst_file)}"
        label = f"{cu.fore.MAGENTA}\nJob {job.idx}: {src_label}{cu.fore.MAGENTA} -> {dst_label}"
        print(label)
        print('-' * len(label))

    def _get_stream_indexes(self, job, select_streams):
        src_media_info = FFmpeg.get_clean_probe_info(job.src_file)
        dst_media_info = FFmpeg.get_clean_probe_info(job.dst_file)

        """"Get source and sync target media stream indexes"""
        src_aud_streams = Stream.get_audio_streams_from_probe(src_media_info['audio']) if 'audio' in src_media_info else []
        src_sub_streams = Stream.get_sub_streams_from_probe(src_media_info['subtitle']) if 'subtitle' in src_media_info else []
        dst_aud_streams = Stream.get_audio_streams_from_probe(dst_media_info['audio']) if 'audio' in dst_media_info else []

        if select_streams:
            self._show_stream_select_header(job)

        def _select_stream(streams, prompt, isTarget=False):
            return self._get_stream_choice(streams, prompt, isTarget) if select_streams else streams[0]

        src_aud_selected = _select_stream(src_aud_streams, "Select a source audio stream: ")
        src_sub_selected = _select_stream(src_sub_streams, "Select a source subtitle stream: ")
        dst_aud_selected = _select_stream(dst_aud_streams, "Select a target audio stream: ", isTarget=True)
        
        streams_info = {
            "src_aud_id": src_aud_selected.id,
            "src_aud_display": src_aud_selected.display_name,
            "dst_aud_id": dst_aud_selected.id,
            "dst_aud_display": dst_aud_selected.display_name,
            "src_sub_id": src_sub_selected.id,
            "src_sub_display": src_sub_selected.display_name,
            "src_sub_lang": Stream.get_stream_lang(src_sub_streams, src_sub_selected.id),
            "src_sub_name": Stream.get_stream_name(src_sub_streams, src_sub_selected.id),
            "src_sub_ext": Stream.get_subtitle_extension(src_sub_streams, src_sub_selected.id),
            "dst_vid_width": dst_media_info.get('video', [{}])[0].get('width'),
            "dst_vid_height": dst_media_info.get('video', [{}])[0].get('height')
        }
        return streams_info

    def _set_stream_indexes(self, unqueued_jobs):
        """"Set audio and subtitle track indexes for video sync jobs"""
        if len(unqueued_jobs) > 1 and confirm_prompt.get("Set tracks from first job as default?", suffix=" (Y/N = choose per job): ", nl_before=True):
            default_indexes = self._get_stream_indexes(unqueued_jobs[0], True) # Use first job as reference
            for job in unqueued_jobs:
                job.__dict__.update(default_indexes)
        else:
            for job in unqueued_jobs:
                indexes = self._get_stream_indexes(job, True)
                job.__dict__.update(indexes)
