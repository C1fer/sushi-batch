from pathlib import Path

from ..models.stream import AudioStream, SubtitleStream
from ..models.job.video_sync_job import VideoSyncJob

from ..ui.prompts import choice_prompt, confirm_prompt
from ..utils import console_utils as cu
from ..utils import utils


class JobStreamSelectionService:
    @classmethod
    def _get_stream_choice(cls, streams: list[AudioStream] | list[SubtitleStream], prompt: str, is_target: bool = False) -> int:
        """Get user-selected stream from list. Skips selection if only one stream is available."""
        if len(streams) == 1:
            print(prompt)
            stream_color = cu.fore.YELLOW if is_target else cu.fore.LIGHTBLUE_EX
            stream_label = f"{stream_color}{streams[0].display_label}"
            cu.print_warning(f"{cu.fore.LIGHTBLACK_EX}Only 1 stream available. Automatically selected: {stream_label}", wait=False)
            return streams[0].id

        options = [(int(stream.id), stream.display_label) for stream in streams]
        selected_stream_id = choice_prompt.get(prompt, options)
        return selected_stream_id

    @classmethod
    def _select_streams(cls, job: VideoSyncJob) -> tuple[int, int, int]:
        """Select source and sync target media streams for a given job (supports manual stream selection)."""
        src_label = f"{cu.fore.LIGHTBLUE_EX}{Path(job.src_filepath).name}"
        dst_label = f"{cu.fore.YELLOW}{Path(job.dst_filepath).name}"
        label = f"{cu.fore.MAGENTA}\nJob {job.id}: {src_label}{cu.fore.MAGENTA} -> {dst_label}"
        print(label)
        print("-" * len(label))

        src_aud_selected = cls._get_stream_choice(job.src_streams.audio, "Select a source audio stream: ")
        src_sub_selected = cls._get_stream_choice(job.src_streams.subtitle, "Select a source subtitle stream: ")
        dst_aud_selected = cls._get_stream_choice(job.dst_streams.audio, "Select a target audio stream: ", is_target=True)
        return src_aud_selected, src_sub_selected, dst_aud_selected

    @classmethod
    def _set_streams_for_job(cls, job: VideoSyncJob) -> None:
        """Set source and target media streams for a given job."""
        src_aud_id, src_sub_id, dst_aud_id = utils.interrupt_signal_handler(cls._select_streams)(job)
        job.src_streams.set_selected_audio_stream_by_id(src_aud_id)
        job.src_streams.set_selected_subtitle_stream_by_id(src_sub_id)
        job.dst_streams.set_selected_audio_stream_by_id(dst_aud_id)

    @classmethod
    def _handle_manual_stream_selection(cls, unqueued_jobs: list[VideoSyncJob]):
        """Set audio and subtitle streams for video sync jobs manually."""
        use_default: bool = len(unqueued_jobs) > 1 and confirm_prompt.get(
            "Set tracks from first job as default?",
            suffix=" (Y = apply to all jobs, N = choose per job): ",
            nl_before=True,
        )

        if use_default:
            default_src_aud_id, default_src_sub_id, default_dst_aud_id = utils.interrupt_signal_handler(cls._select_streams)(unqueued_jobs[0])
            for job in unqueued_jobs: 
                try:
                    job.src_streams.set_selected_audio_stream_by_id(default_src_aud_id)
                    job.src_streams.set_selected_subtitle_stream_by_id(default_src_sub_id)
                    job.dst_streams.set_selected_audio_stream_by_id(default_dst_aud_id)
                except ValueError as e:
                    cu.print_error(f"Cannot set default streams for job: {e}", nl_before=True)
                    cls._set_streams_for_job(job)
        else:
            for job in unqueued_jobs:
                cls._set_streams_for_job(job)
    
    @classmethod
    def set_video_sync_job_streams(cls, jobs_to_queue: list[VideoSyncJob]):
        """Set audio and subtitle streams for video sync jobs"""
        if confirm_prompt.get("Choose source and target tracks manually?", suffix=" (Y = manual, N = first available): ", nl_before=True):
            cls._handle_manual_stream_selection(jobs_to_queue)
        else:
            for job in jobs_to_queue:
                job.src_streams.audio[0].selected = True
                job.src_streams.subtitle[0].selected = True
                job.dst_streams.audio[0].selected = True
                
