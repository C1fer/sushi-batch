import subprocess
from io import TextIOWrapper

from yaspin.core import Yaspin

from ..external.execution_logger import ExecutionLogger
from ..models import settings as s
from ..models.enums import AudioChannelLayout, AudioEncodeCodec, AudioEncoder
from ..models.job.video_sync_job import VideoSyncJob
from ..models.stream import AudioStream
from ..utils import console_utils as cu
from ..utils import utils
from ..utils.constants import FFPROBE_CHANNEL_LAYOUT_MAP
from .ffmpeg import FFmpeg


class XiphOpusEncoder:
    is_available: bool = utils.is_app_installed("opusenc")
    log_section_name: str = "Audio Encode"

    @classmethod
    def encode(
        cls,
        job: VideoSyncJob,
        stream: AudioStream,
        spinner: Yaspin | None = None,
        log_prefix="[Opusenc]",
    ) -> str | None:
        """Encodes audio with opusenc using the codec settings. Pipes decoded audio from FFmpeg to opusenc and saves to *_encode.opus."""
        log_fd: TextIOWrapper | int = subprocess.DEVNULL
        try:
            layout_enum: AudioChannelLayout | None = next((layout for layout in FFPROBE_CHANNEL_LAYOUT_MAP.keys() if stream.channel_layout in FFPROBE_CHANNEL_LAYOUT_MAP[layout]), None)
            if not layout_enum:
                cu.print_warning(f"{log_prefix} Unknown or unsupported channel layout '{stream.channel_layout}'. Defaulting to stereo.", nl_before=False, wait=False)
                layout_enum = AudioChannelLayout.STEREO
            
            layout_bitrate: str = s.config.merge_workflow["encode_codec_settings"][AudioEncodeCodec.OPUS.name]["bitrates"][layout_enum.name]
            output_path: str = f"{job.dst_filepath}_track{stream.id}_encode.opus"
            encode_args: list[str] =  [
                "opusenc",
                "--bitrate", layout_bitrate.replace("k", ""),
                "--vbr",
                "-",
                output_path
            ]

            bitrate_display: str = layout_bitrate.replace('k', ' kbps')
            out_info = f"Opus ({bitrate_display})"

            displayed_message: str = f"Encoding audio track {stream.short_display_label} to {out_info}"
            if spinner:
                spinner.text = f"{log_prefix} {displayed_message}"
            else:
                cu.print_warning(f"{log_prefix} {displayed_message}", nl_before=False, wait=False)

            pipe_args: list[str] = FFmpeg.get_pcm_pipe_args(job.dst_filepath, stream.id)

            # Logs are written directly to file to avoid the risk of stderr pipe crashing if piped stream is too large
            log_fd = open(job.merge.log_path, "a", encoding="utf-8", errors="replace") if job.merge.log_path else subprocess.DEVNULL
            if isinstance(log_fd, TextIOWrapper):
                ffmpeg_args_log: str = f"{ExecutionLogger.internal_log_indicator}Piping stream to opusenc with arguments: {(' '.join(pipe_args))}\n\n"
                opusenc_args_log: str = f"{ExecutionLogger.internal_log_indicator}Running with arguments: {(' '.join(encode_args))}\n\n"
                ExecutionLogger.save_log_output_to_fd(log_fd, ffmpeg_args_log + opusenc_args_log, section_name=cls.log_section_name)

            # Decode audio stream from FFmpeg to PCM pipe
            ffmpeg_pipe_process = subprocess.Popen(
                pipe_args, 
                stdout=subprocess.PIPE, 
                stderr=log_fd,
                text=True,
                encoding="utf-8",
                errors="replace",
            )

            encode_process = subprocess.Popen(
                encode_args,
                stdin=ffmpeg_pipe_process.stdout,
                stderr=log_fd,
                text=True,
                encoding="utf-8",
                errors="replace",
            )

            # Close pipe when opusenc exits
            if ffmpeg_pipe_process.stdout:
                ffmpeg_pipe_process.stdout.close()

            encode_process.communicate()
            if encode_process.returncode != 0:
                return None
        
            stream.encoded = True
            stream.encode_path = output_path
            stream.encode_bitrate = bitrate_display

            job.merge.audio_encode_done = True
            job.merge.audio_encode_codec = AudioEncodeCodec.OPUS.name
            job.merge.audio_encode_encoder = AudioEncoder.XIPH_OPUSENC.name
            
            cu.try_print_spinner_message(f"{cu.fore.LIGHTGREEN_EX}{log_prefix} Track {stream.short_display_label} successfully encoded to {out_info}.", spinner)
            return output_path
        except Exception as e:
            _message: str = f"An error occurred while encoding audio track {stream.short_display_label}: {e}"
            if isinstance(log_fd, TextIOWrapper):
                ExecutionLogger.save_log_output_to_fd(log_fd, _message, section_name=cls.log_section_name)
            cu.try_print_spinner_message(f"{cu.fore.LIGHTRED_EX}{log_prefix} {_message}", spinner)
        finally:
            if isinstance(log_fd, TextIOWrapper):
                log_fd.close()
