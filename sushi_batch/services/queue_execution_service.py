from ..external.ffmpeg import FFmpeg
from ..external.mkv_merge import MKVMerge
from ..external.opusenc import XiphOpusEncoder
from ..external.sub_resample import SubResampler
from ..external.sub_sync import Sushi
from ..models import settings
from ..models.enums import AudioEncoder, Status
from ..ui.prompts import input_prompt
from ..utils import console_utils as cu
from ..utils import constants, utils


class QueueExecutionService:
    @classmethod
    def _run_sub_sync(cls, job, use_advanced_sushi_args, parent_queue):
        """Run Sushi subtitle sync for a given job."""
        Sushi.run(job, use_advanced_args=use_advanced_sushi_args)
        parent_queue.save()

    @classmethod
    def run_jobs(cls, jobs_to_run, use_advanced_sushi_args=False, parent_queue=None):
        """Orchestrate the execution of sync jobs and optionally merge completed video jobs."""
        try:
            if not jobs_to_run:
                cu.print_error("No pending jobs to run!", nl_before=True)
                return

            cu.print_subheader("Running synchronization jobs")

            completed_video_jobs = []
            for job in jobs_to_run:
                utils.interrupt_signal_handler(cls._run_sub_sync)(job, use_advanced_sushi_args, parent_queue)
                if job.sync_status == Status.COMPLETED and job.task in constants.VIDEO_TASKS:
                    completed_video_jobs.append(job)

            can_merge = settings.config.merge_workflow.get("merge_files_after_execution") and completed_video_jobs
            if can_merge:
                if MKVMerge.is_installed:
                    cls.merge_completed_video_jobs(completed_video_jobs, parent_queue=parent_queue)
                else:
                    cu.print_error("MKVMerge could not be found. Video files cannot be merged.", nl_before=True)

            input_prompt.get("All jobs have been processed. Press Enter to continue... ", success=True, nl_before=True, allow_empty=True)
        except Exception as e:
            cu.print_error(f"Error running jobs: {e}")

    @classmethod
    def _resample_before_merge(cls, job):
        """Resample subtitle file before merging, when needed."""
        if not SubResampler.is_resample_needed(job):
            return False

        log_prefix = f"[Job {job.idx} - SubResampler]"

        resample_done = SubResampler.run(job)
        if resample_done:
            cu.print_success(f"{log_prefix} Resampling completed successfully.", nl_before=False, wait=False)
            return True

        cu.print_warning(f"{log_prefix} Subtitle could not be resampled. Merging synced subtitle instead.", nl_before=False, wait=False)
        return False

    @classmethod
    def _encode_audio_before_merge(cls, job):
        """Encode audio before merge if configured and needed."""
        if not FFmpeg.is_audio_encode_needed(job):
            return None

        selected_codec = settings.config.merge_workflow.get("encode_codec")
        selected_encoder = settings.config.merge_workflow.get("encode_codec_settings", {}).get(selected_codec.name, {}).get("encoder")

        log_prefix = f"[Job {job.idx} - Audio Encoder]"

        match selected_encoder:
            case AudioEncoder.XIPH_OPUSENC:
                if not XiphOpusEncoder.is_available:
                    cu.print_error(f"{log_prefix} Could not find Opusenc. Using FFmpeg instead.", nl_before=False, wait=False)
                    output_path = FFmpeg.encode_lossless_audio(job)
                else:
                    output_path = XiphOpusEncoder.encode(job)
            case AudioEncoder.LIBOPUS_FFMPEG:
                output_path = FFmpeg.encode_lossless_audio(job)

        if output_path:
            cu.print_success(f"{log_prefix} Audio track encoded successfully.", nl_before=False, wait=False)
            return output_path

        cu.print_warning(f"{log_prefix} Audio track could not be encoded. Merging original audio track instead.", nl_before=False, wait=False)
        return None

    @classmethod
    def _run_merge(cls, job, do_resample, do_encode_audio, parent_queue):
        """Execute the merging process for a given job. Handles audio encoding and subtitle resampling if needed."""
        encoded_audio_path = cls._encode_audio_before_merge(job) if do_encode_audio else None
        use_resampled_sub = cls._resample_before_merge(job) if do_resample else False
        MKVMerge.run(job, use_resampled_sub=use_resampled_sub, encoded_audio_path=encoded_audio_path)
        parent_queue.save()

    @classmethod
    def merge_completed_video_jobs(cls, selected_jobs=None, parent_queue=None):
        """Orchestrate the merging of selected video jobs."""
        if not selected_jobs:
            cu.print_error("No completed jobs to merge!")
            return

        cu.print_subheader("Merging files")

        do_audio_encode = settings.config.merge_workflow.get("encode_lossless_audio_before_merging")
        do_resample = True
        if settings.config.merge_workflow.get("resample_subs_on_merge") and not SubResampler.is_installed:
            do_resample = False
            cu.print_error("Aegisub-CLI could not be found. Subtitle resampling will be skipped.")

        for job in selected_jobs:
            utils.interrupt_signal_handler(cls._run_merge)(job, do_resample, do_audio_encode, parent_queue)

        if settings.config.merge_workflow.get("delete_generated_files_after_merge"):
            successfully_merged_jobs = [job for job in selected_jobs if job.merged]
            parent_queue._clean_generated_files(successfully_merged_jobs, confirm_deletion=False)

        input_prompt.get("Merging process completed. Press Enter to continue... ", success=True, allow_empty=True, nl_before=True)
