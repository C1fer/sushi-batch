import subprocess

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
    log_section_name: str = "Audio Encode (Opusenc)"

    @classmethod
    def _try_save_log_content(cls, content: str, log_path: str | None = None, section_name: str | None = None, is_internal: bool = False) -> None:
        if s.config.general["save_merge_logs"] and log_path:
            _section_name: str = section_name or cls.log_section_name
            ExecutionLogger.save_log_output(log_path, content, section_name= _section_name, is_internal=is_internal)
    
    @classmethod
    def encode(
        cls,
        job: VideoSyncJob,
        stream: AudioStream,
        spinner: Yaspin | None = None,
        log_prefix="[Opusenc]",
        log_path: str | None = None,
    ) -> str | None:
        """Encodes audio with opusenc using the codec settings. Pipes decoded audio from FFmpeg to opusenc and saves to *_encode.opus."""
        track_info: str = f"ID {stream.id}: {stream.title} ({stream.channel_layout})" if not stream.title.isspace() else f"ID {stream.id} ({stream.channel_layout})"
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

            displayed_message: str = f"Encoding audio track {track_info} to {out_info}"
            if spinner:
                spinner.text = f"{log_prefix} {displayed_message}"
            else:
                cu.print_warning(f"{log_prefix} {displayed_message}", nl_before=False, wait=False)
            
            # Pipe decoded audio streams from FFmpeg to opusenc
            ffmpeg_pipe_process = subprocess.Popen(
                FFmpeg.get_pcm_pipe_args(job), 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
            )

            encode_process = subprocess.Popen(
                encode_args,
                stdin=ffmpeg_pipe_process.stdout,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
            )

            ffmpeg_log: str = ffmpeg_pipe_process.stderr.read() if ffmpeg_pipe_process.stderr else ""
            if ffmpeg_log:
                ffmpeg_log += "\n"

            # Close pipes when opusenc exits
            if ffmpeg_pipe_process.stdout:
                ffmpeg_pipe_process.stdout.close()
            if ffmpeg_pipe_process.stderr:
                ffmpeg_pipe_process.stderr.close()

            _, opusenc_stderr = encode_process.communicate()

            opusenc_log = f"{ExecutionLogger.internal_log_indicator}Running with arguments: {(' '.join(encode_args))}\n\n{opusenc_stderr}"

            cls._try_save_log_content(content=opusenc_log, log_path=log_path, section_name=cls.log_section_name)

            if encode_process.returncode != 0:
                return None
            
            cu.try_print_spinner_message(f"{cu.fore.LIGHTGREEN_EX}{log_prefix} Track {track_info} successfully encoded to {out_info}.", spinner)

            stream.encoded = True
            stream.encode_path = output_path
            stream.encode_bitrate = bitrate_display

            job.merge.audio_encode_done = True
            job.merge.audio_encode_codec = AudioEncodeCodec.OPUS.name
            job.merge.audio_encode_encoder = AudioEncoder.XIPH_OPUSENC.name
            return output_path
        except Exception as e:
            _message: str = f"An error occurred while encoding audio track {track_info}: {e}"
            cls._try_save_log_content(content=_message, log_path=log_path, section_name=cls.log_section_name)
            cu.try_print_spinner_message(f"{cu.fore.LIGHTRED_EX}{log_prefix} {_message}", spinner)
