from os import path

from ..external.ffmpeg import FFmpeg
from ..models.streams import Stream
from ..ui.prompts import choice_prompt, confirm_prompt
from ..utils import console_utils as cu
from ..utils import utils


class JobStreamSelectionService:
    @classmethod
    def _get_stream_choice(cls, streams, prompt, is_target=False):
        """Get user-selected stream from list. Skips selection if only one stream is available."""
        if len(streams) == 1:
            print(prompt)
            stream_color = cu.fore.YELLOW if is_target else cu.fore.LIGHTBLUE_EX
            stream_label = f"{stream_color}{streams[0].display_name}"
            cu.print_warning(f"{cu.fore.LIGHTBLACK_EX}Only 1 stream available. Automatically selected: {stream_label}", wait=False)
            return streams[0]

        options = [(int(stream.id), stream.display_name) for stream in streams]
        selected_stream_id = choice_prompt.get(prompt, options)
        return next(stream for stream in streams if int(stream.id) == selected_stream_id)

    @classmethod
    def _show_stream_select_header(cls, job):
        """Show stream selection header for a job. Used to separate job streams in the console output."""
        src_label = f"{cu.fore.LIGHTBLUE_EX}{path.basename(job.src_file)}"
        dst_label = f"{cu.fore.YELLOW}{path.basename(job.dst_file)}"
        label = f"{cu.fore.MAGENTA}\nJob {job.idx}: {src_label}{cu.fore.MAGENTA} -> {dst_label}"
        print(label)
        print("-" * len(label))

    @classmethod
    def _get_job_streams(cls, job, do_select_streams=False):
        """Retrieve source and sync target media streams for a given job (supports manual stream selection)."""
        src_media_info = FFmpeg.get_clean_probe_info(job.src_file)
        dst_media_info = FFmpeg.get_clean_probe_info(job.dst_file)

        src_aud_streams = Stream.get_audio_streams_from_probe(src_media_info["audio"]) if "audio" in src_media_info else []
        src_sub_streams = Stream.get_sub_streams_from_probe(src_media_info["subtitle"]) if "subtitle" in src_media_info else []
        dst_aud_streams = Stream.get_audio_streams_from_probe(dst_media_info["audio"]) if "audio" in dst_media_info else []

        if do_select_streams:
            cls._show_stream_select_header(job)
            src_aud_selected = cls._get_stream_choice(src_aud_streams, "Select a source audio stream: ")
            src_sub_selected = cls._get_stream_choice(src_sub_streams, "Select a source subtitle stream: ")
            dst_aud_selected = cls._get_stream_choice(dst_aud_streams, "Select a target audio stream: ", is_target=True)   
        else:
            src_aud_selected = src_aud_streams[0]
            src_sub_selected = src_sub_streams[0]
            dst_aud_selected = dst_aud_streams[0]

        return {
            "src_aud_id": src_aud_selected.id,
            "src_aud_display": src_aud_selected.display_name,
            "src_sub_id": src_sub_selected.id,
            "src_sub_display": src_sub_selected.display_name,
            "src_sub_lang": src_sub_selected.lang,
            "src_sub_name": src_sub_selected.title,
            "src_sub_ext": Stream.get_subtitle_extension(src_sub_streams, src_sub_selected.id),
            "dst_aud_id": dst_aud_selected.id,
            "dst_aud_display": dst_aud_selected.display_name,
            "dst_aud_codec": dst_aud_selected.codec,
            "dst_aud_lang": dst_aud_selected.lang,
            "dst_aud_channel_layout": dst_aud_selected.channel_layout,
            "dst_vid_width": dst_media_info.get("video", [{}])[0].get("width"),
            "dst_vid_height": dst_media_info.get("video", [{}])[0].get("height"),
        }

    @classmethod
    def _handle_manual_stream_selection(cls, unqueued_jobs):
        """Set audio and subtitle streams for video sync jobs manually."""
        use_default = len(unqueued_jobs) > 1 and confirm_prompt.get(
            "Set tracks from first job as default?",
            suffix=" (Y = apply to all jobs, N = choose per job): ",
            nl_before=True,
        )
        if use_default:
            default_streams = utils.interrupt_signal_handler(cls._get_job_streams)(unqueued_jobs[0], do_select_streams=True)
            for job in unqueued_jobs:
                job.__dict__.update(default_streams)
            return

        for job in unqueued_jobs:
            streams = utils.interrupt_signal_handler(cls._get_job_streams)(job, do_select_streams=True)
            job.__dict__.update(streams)
    
    @classmethod
    def set_video_sync_job_streams(cls, jobs_to_queue):
        """Set audio and subtitle streams for video sync jobs"""
        if confirm_prompt.get("Choose source and target tracks manually?", suffix=" (Y = manual, N = first available): ", nl_before=True):
            cls._handle_manual_stream_selection(jobs_to_queue)
        else:
            for job in jobs_to_queue:
                streams = cls._get_job_streams(job, do_select_streams=False)
                job.__dict__.update(streams)
