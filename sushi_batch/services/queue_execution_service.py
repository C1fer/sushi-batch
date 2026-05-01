from ..external.ffmpeg import FFmpeg
from ..external.mkv_merge import MKVMerge
from ..external.opusenc import XiphOpusEncoder
from ..external.sub_resample import SubResampler
from ..external.sub_sync import Sushi
from ..models import settings
from ..models.job.audio_sync_job import AudioSyncJob
from ..models.job.video_sync_job import VideoSyncJob
from ..models.job_queue import JobQueue
from ..models.enums import AudioEncoder, Status
from ..ui.prompts import input_prompt
from ..utils import console_utils as cu
from ..utils import utils
from yaspin import yaspin
from yaspin.core import Yaspin
from ..external.execution_logger import ExecutionLogger


class QueueExecutionService:
    @classmethod
    def _run_sub_sync(cls, job: AudioSyncJob | VideoSyncJob, use_advanced_sushi_args: bool = False, parent_queue: JobQueue | None = None) -> None:
        """Run Sushi subtitle sync for a given job."""
        log_prefix = f"[Job {job.id} - Sushi]"
        Sushi.run(job, use_advanced_args=use_advanced_sushi_args, log_prefix=log_prefix)
        if parent_queue:
            parent_queue.save()

    @classmethod
    def run_jobs(cls, jobs_to_run: list[AudioSyncJob | VideoSyncJob], use_advanced_sushi_args: bool = False, parent_queue: JobQueue | None = None) -> None:
        """Orchestrate the execution of sync jobs and optionally merge completed video jobs."""
        try:
            if not jobs_to_run:
                cu.print_error("No pending jobs to run!", nl_before=True)
                return

            cu.print_subheader("Running synchronization jobs")

            completed_video_jobs: list[VideoSyncJob] = []
            for job in jobs_to_run:
                utils.interrupt_signal_handler(cls._run_sub_sync)(job, use_advanced_sushi_args, parent_queue)
                if job.sync.status == Status.COMPLETED and isinstance(job, VideoSyncJob):
                    completed_video_jobs.append(job)

            can_merge = settings.config.merge_workflow.get("merge_files_after_execution") and bool(completed_video_jobs)
            if can_merge:
                if MKVMerge.is_installed:
                    cls.merge_completed_video_jobs(completed_video_jobs, parent_queue=parent_queue, display_confirmation=False)
                else:
                    cu.print_error("MKVMerge could not be found. Video files cannot be merged.", nl_before=True)

            input_prompt.get("All jobs have been processed. Press Enter to continue... ", success=True, nl_before=True, allow_empty=True)
        except Exception as e:
            cu.print_error(f"Error running jobs: {e}")

    @classmethod
    def _resample_before_merge(cls, job: VideoSyncJob, spinner: Yaspin | None = None, log_path: str | None = None) -> bool:
        """Resample subtitle file before merging, when needed."""
        log_prefix = f"[Job {job.id} - Sub Resampler]"
        if not SubResampler.is_resample_needed(job, spinner=spinner, log_prefix=log_prefix, log_path=log_path):
            return False

        resample_done = SubResampler.run(job, spinner=spinner, log_prefix=log_prefix, log_path=log_path)
        if not resample_done:
            cu.try_print_spinner_message(f"{cu.fore.LIGHTYELLOW_EX}{log_prefix} Subtitle could not be resampled. Merging synced subtitle instead.", spinner)
            return False
        return True

    @classmethod
    def _encode_audio_before_merge(cls, job: VideoSyncJob, spinner: Yaspin | None = None, log_path: str | None = None) -> str | None:
        """Encode audio before merge if configured and needed."""
        selected_codec = settings.config.merge_workflow.get("encode_codec")
        selected_encoder = settings.config.merge_workflow.get("encode_codec_settings", {}).get(selected_codec.name, {}).get("encoder")
       
        log_prefix = f"[Job {job.id} - FFmpeg]" if selected_encoder != AudioEncoder.XIPH_OPUSENC else f"[Job {job.id} - Opusenc]"

        if not FFmpeg.is_audio_encode_needed(job, spinner=spinner, log_prefix=log_prefix, log_path=log_path):
            return None

        match selected_encoder:
            case AudioEncoder.XIPH_OPUSENC:
                if XiphOpusEncoder.is_available:
                    output_path = XiphOpusEncoder.encode(job, spinner=spinner, log_prefix=log_prefix, log_path=log_path)
                else:
                    cu.try_print_spinner_message(f"{cu.fore.LIGHTRED_EX}{log_prefix} Could not find opusenc. Encoding with FFmpeg instead.", spinner)
                    log_prefix = f"[Job {job.id} - FFmpeg]"
                    output_path = FFmpeg.encode_lossless_audio(job, spinner=spinner, log_prefix=log_prefix, is_fallback=True, log_path=log_path)
            case _:
                output_path = FFmpeg.encode_lossless_audio(job, spinner=spinner, log_prefix=log_prefix, log_path=log_path)

        if not output_path:
            cu.try_print_spinner_message(f"{cu.fore.LIGHTYELLOW_EX}{log_prefix} Audio track could not be encoded. Merging original audio track instead.", spinner)
            return None
        return output_path

    @classmethod
    def _run_merge(cls, job: VideoSyncJob, do_resample: bool = False, do_encode_audio: bool = False, parent_queue: JobQueue | None = None) -> None:
        """Execute the merging process for a given job. Handles audio encoding and subtitle resampling if needed."""
        with yaspin(text="", color="cyan", timer=True, ellipsis="...") as sp:
            log_path = ExecutionLogger.set_log_path(job.dst_filepath, "Merge Logs") if settings.config.general.get("save_merge_logs") else None
            encoded_audio_path = cls._encode_audio_before_merge(job, spinner=sp, log_path=log_path) if do_encode_audio else None
            use_resampled_sub = cls._resample_before_merge(job, spinner=sp, log_path=log_path) if do_resample else False
            MKVMerge.run(
                job,
                use_resampled_sub=use_resampled_sub,
                encoded_audio_path=encoded_audio_path,
                spinner=sp,
                log_prefix=f"[Job {job.id} - MKVMerge]",
                log_path=log_path,
            )
            if parent_queue:
                parent_queue.save()

    @classmethod
    def merge_completed_video_jobs(cls, selected_jobs: list[VideoSyncJob], parent_queue: JobQueue | None = None, display_confirmation: bool = True) -> None:
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
            print()

        if settings.config.merge_workflow.get("delete_generated_files_after_merge"):
            successfully_merged_jobs = [job for job in selected_jobs if job.merge.done]
            if parent_queue:
                parent_queue.clean_generated_files(successfully_merged_jobs, confirm_deletion=False)

        if display_confirmation:
            input_prompt.get("Merging process completed. Press Enter to continue... ", success=True, allow_empty=True, nl_before=True)
        else:
            cu.print_success("Merging process completed.", nl_before=True)
