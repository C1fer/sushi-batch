from sushi_batch.models.stream import AudioStream
from ..external.ffmpeg import FFmpeg
from ..external.mkv_merge import MKVMerge
from ..external.opusenc import XiphOpusEncoder
from ..external.sub_resample import SubResampler
from ..external.sub_sync import Sushi
from ..models import settings as s
from ..models.job.audio_sync_job import AudioSyncJob
from ..models.job.video_sync_job import VideoSyncJob
from ..models.job_queue import JobQueue, JobQueueContents
from ..models.enums import AudioEncodeCodec, AudioEncoder, Status, TracksToEncode
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

            can_merge: bool = s.config.merge_workflow["merge_files_after_execution"] and bool(completed_video_jobs)
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
    def _encode_audio_before_merge(cls, job: VideoSyncJob, spinner: Yaspin | None = None, log_path: str | None = None) -> None:
        """Encode audio before merge if configured and needed. Returns encoded audio paths."""
        selected_codec: AudioEncodeCodec = s.config.merge_workflow["encode_codec"]
        selected_encoder: AudioEncoder = s.config.merge_workflow["encode_codec_settings"][selected_codec.name]["encoder"]

        log_prefix: str = (
            f"[Job {job.id} - FFmpeg]"
            if selected_encoder != AudioEncoder.XIPH_OPUSENC
            else f"[Job {job.id} - Opusenc]"
        )

        stream_list: list[AudioStream] = (
            job.dst_streams.audio
            if s.config.merge_workflow["tracks_to_encode_before_merging"] == TracksToEncode.ALL
            else [job.dst_streams.get_selected_audio_stream()]
        )

        tracks_to_encode: list[AudioStream] = [
            stream
            for stream in stream_list
            if  FFmpeg.is_audio_encode_needed(stream, spinner=spinner, log_prefix=log_prefix, log_path=log_path)
        ]
        if not tracks_to_encode:
            return

        use_fallback: bool = False
        for stream in tracks_to_encode:
            match selected_encoder:
                case AudioEncoder.XIPH_OPUSENC if not use_fallback:
                    if XiphOpusEncoder.is_available:
                        output_path: str | None = XiphOpusEncoder.encode(job, stream, spinner=spinner, log_prefix=log_prefix, log_path=log_path)
                    else:
                        cu.try_print_spinner_message(f"{cu.fore.LIGHTRED_EX}{log_prefix} Could not find opusenc. Encoding with FFmpeg instead.", spinner)
                        use_fallback = True
                        log_prefix = f"[Job {job.id} - FFmpeg]"
                        output_path: str | None = FFmpeg.encode_lossless_audio(job, stream, spinner=spinner, log_prefix=log_prefix, is_fallback=use_fallback, log_path=log_path)
                case _:
                    output_path: str | None = FFmpeg.encode_lossless_audio(job, stream, spinner=spinner, log_prefix=log_prefix, is_fallback=use_fallback, log_path=log_path)

            if not output_path:
                cu.try_print_spinner_message(f"{cu.fore.LIGHTYELLOW_EX}{log_prefix} Audio track could not be encoded. Merging original audio track instead.", spinner)
                continue

    @classmethod
    def _run_merge(cls, job: VideoSyncJob, do_resample: bool = False, do_encode_audio: bool = False, parent_queue: JobQueue | None = None) -> None:
        """Execute the merging process for a given job. Handles audio encoding and subtitle resampling if needed."""
        with yaspin(text="", color="cyan", timer=True, ellipsis="...") as sp:
            log_path: str | None = (
                ExecutionLogger.set_log_path(job.dst_filepath, "Merge Logs")
                if s.config.general["save_merge_logs"]
                else None
            )
            cls._encode_audio_before_merge(job, spinner=sp, log_path=log_path) if do_encode_audio else []
            use_resampled_sub: bool = cls._resample_before_merge(job, spinner=sp, log_path=log_path) if do_resample else False
            MKVMerge.run(
                job,
                use_resampled_sub=use_resampled_sub,
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

        do_audio_encode: bool = s.config.merge_workflow["encode_lossless_audio_before_merging"]
        do_resample: bool = True
        if s.config.merge_workflow["resample_subs_on_merge"] and not SubResampler.is_installed:
            do_resample = False
            cu.print_error("Aegisub-CLI could not be found. Subtitle resampling will be skipped.")

        for job in selected_jobs:
            utils.interrupt_signal_handler(cls._run_merge)(job, do_resample, do_audio_encode, parent_queue)
            print()

        if s.config.merge_workflow["delete_generated_files_after_merge"]:
            if isinstance(parent_queue, JobQueue):
                successfully_merged_jobs: JobQueueContents = [job for job in selected_jobs if job.merge.done]
                parent_queue.clean_generated_files(successfully_merged_jobs, confirm_deletion=False)

        if display_confirmation:
            input_prompt.get("Merging process completed. Press Enter to continue... ", success=True, allow_empty=True, nl_before=True)
        else:
            cu.print_success("Merging process completed.", nl_before=True)
