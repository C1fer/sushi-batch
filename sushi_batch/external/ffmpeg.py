import subprocess

from yaspin.core import Yaspin

from ..external.execution_logger import ExecutionLogger
from ..models import settings as s
from ..models.enums import AudioChannelLayout, AudioEncodeCodec, AudioEncoder
from ..models.job.video_sync_job import VideoSyncJob
from ..models.stream import AudioStream
from ..utils import console_utils as cu
from ..utils import utils

LIB_KEY: str = "-c:a"
BITRATE_KEY: str = "-b:a"

LOSSY_AUDIO_CODEC_PARAMS: dict[AudioEncodeCodec, dict[str, str]] = {
    AudioEncodeCodec.OPUS: { # Approximated to opusenc default params
        LIB_KEY: "",
        BITRATE_KEY: "",
        "-vbr": "on",
        "-af": "asetpts=N/SR/TB", # Ensure proper timestamp handling, soxr: high quality resampling to opus standard freq. rate (48kHz)
        "-compression_level": "10",
        "-application": "audio",
        "-frame_duration": "20",
        "-map_chapters": "-1", # Exclude chapters to avoid issues when merging back with mkvmerge
    },
    AudioEncodeCodec.AAC: {
        LIB_KEY: "",
        BITRATE_KEY: "",
        "-q:a": "2",
        "-profile:a": "aac_low"
    },
    AudioEncodeCodec.EAC3: {
        LIB_KEY: "",
        BITRATE_KEY: ""
    }
}

LOSSLESS_AUDIO_CODECS: set[str] = {"flac", "pcm", "wav"}

PROBE_CHANNEL_LAYOUT_MAP: dict[str, AudioChannelLayout] = {
    "mono": AudioChannelLayout.MONO,
    "stereo": AudioChannelLayout.STEREO,
    "5.1": AudioChannelLayout.SURROUND_5_1,
    "7.1": AudioChannelLayout.SURROUND_7_1,
}

ENCODER_LIB_MAP: dict[AudioEncoder, str]  = {
    AudioEncoder.AAC_FFMPEG: "aac",
    AudioEncoder.EAC3_FFMPEG: "eac3",
    AudioEncoder.LIBOPUS_FFMPEG: "libopus",
}

FALLBACK_ENCODERS: dict[AudioEncoder, AudioEncoder] = { AudioEncoder.XIPH_OPUSENC: AudioEncoder.LIBOPUS_FFMPEG }

class FFmpeg:
    is_installed: bool = utils.is_app_installed("ffmpeg")
    log_section_name = "Audio Encode (FFmpeg)"

    @classmethod
    def _try_save_log_content(cls, log_path: str | None, content: str, section_name: str | None = None, is_internal: bool = False):
        if s.config.general["save_merge_logs"] and log_path:
            _section_name: str = section_name or cls.log_section_name
            ExecutionLogger.save_log_output(log_path, content, section_name= _section_name, is_internal=is_internal)

    @classmethod
    def _get_codec_params(cls, job: VideoSyncJob, settings_codec: AudioEncodeCodec, settings_encoder: AudioEncoder) -> tuple[list[str], str]:
        ffmpeg_codec_params: dict[str, str] = LOSSY_AUDIO_CODEC_PARAMS.get(settings_codec, {})
        if not ffmpeg_codec_params:
            raise ValueError(f"Unsupported audio codec selected for encoding: {settings_codec.name}")

        track_layout: str = job.dst_streams.get_selected_audio_stream().channel_layout
        layout_enum: AudioChannelLayout | None = PROBE_CHANNEL_LAYOUT_MAP.get(track_layout, None)
        if not layout_enum:
            cu.print_warning(f"[Job {job.id} - FFmpeg] Unknown or unsupported channel layout '{track_layout}'. Defaulting to stereo.", nl_before=False, wait=False)
            layout_enum = AudioChannelLayout.STEREO

        selected_bitrate: str | None = s.config.merge_workflow["encode_codec_settings"][settings_codec.name]["bitrates"].get(layout_enum.name)
        encoder_lib = ENCODER_LIB_MAP.get(settings_encoder)
        if not encoder_lib:
            raise ValueError(f"No FFmpeg library mapping for encoder: {settings_encoder.name}")
        if not selected_bitrate:
            raise ValueError(f"No bitrate configured for {settings_codec.name} / layout {layout_enum.name}")

        ffmpeg_codec_params.update({LIB_KEY: encoder_lib, BITRATE_KEY: selected_bitrate})

        args: list[str] = []
        for key, value in ffmpeg_codec_params.items():
            args.extend([key, value])
        return args, selected_bitrate
    
    @classmethod
    def _get_audio_encode_args(cls, job: VideoSyncJob, settings_codec: AudioEncodeCodec, settings_encoder: AudioEncoder) -> tuple[list[str], str, str]:
        """Constructs ffmpeg arguments for encoding audio with the selected codec."""
        output_path: str = f"{job.dst_filepath}_encode.{settings_codec.name.lower()}"
        codec_params, selected_bitrate = cls._get_codec_params(job, settings_codec, settings_encoder)
        
        args: list[str] = [
            'ffmpeg',
            '-i', job.dst_filepath,
            '-map', f'0:{job.dst_streams.get_selected_audio_stream().id}',
            *codec_params,
            '-y',  # Overwrite output file if it exists
            output_path
        ]
        return args, output_path, selected_bitrate

    @classmethod
    def get_clean_audio_encode_log(cls, content: str) -> str:
        """Returns the clean audio encode log by removing input metadata"""
        try:
            version_info: list[str] = content.split("Input #0")
            if len(version_info) < 2:
                return content
            output_info: list[str] = version_info[1].split("Press [q] to stop, [?] for help")
            if len(output_info) < 2:
                return content
            return version_info[0] + output_info[1]
        except Exception:
            return content
    
    @classmethod
    def encode_lossless_audio(cls, job: VideoSyncJob, spinner: Yaspin | None = None, log_prefix="[FFmpeg]", is_fallback: bool = False, log_path: str | None = None) -> str | None:
        """Encodes audio with the selected codec option and saves to *_encode.<ext>."""
        try:
            settings_codec: AudioEncodeCodec = s.config.merge_workflow["encode_codec"]
            selected_encoder: AudioEncoder = s.config.merge_workflow["encode_codec_settings"][settings_codec.name]["encoder"]

            if is_fallback:
                selected_encoder: AudioEncoder | None = FALLBACK_ENCODERS.get(selected_encoder)
                if not selected_encoder:
                    raise ValueError(f"No fallback encoder found for {settings_codec.name}")

            args, output_path, selected_bitrate = cls._get_audio_encode_args(job, settings_codec, selected_encoder)

            bitrate_display: str = selected_bitrate.replace('k', ' kbps')
            out_info = f"{settings_codec.value} ({bitrate_display})"

            if spinner:
                spinner.text = f"{log_prefix} Encoding audio track to {out_info}"
            else:
                cu.print_warning(f"{log_prefix} Encoding audio track to {out_info}", nl_before=False, wait=False)
           
            ffmpeg_encode = subprocess.Popen(
                args,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            _, stderr = ffmpeg_encode.communicate()

            ffmpeg_log: str = cls.get_clean_audio_encode_log(stderr)
            args_log = f"{ExecutionLogger.internal_log_indicator}Running with arguments: {(' '.join(args))}\n\n"
            cls._try_save_log_content(log_path, args_log + ffmpeg_log)

            if ffmpeg_encode.returncode != 0:
                return None

            cu.try_print_spinner_message(f"{cu.fore.LIGHTGREEN_EX}{log_prefix} Audio track successfully encoded to {out_info}.", spinner)

            job.merge.audio_encode_done = True
            job.merge.audio_encode_codec = settings_codec.name
            job.merge.audio_encode_bitrate = bitrate_display
            job.merge.audio_encode_encoder = selected_encoder.name
            return output_path
        except Exception as e:
            cu.try_print_spinner_message(f"{cu.fore.LIGHTRED_EX}{log_prefix} An error occurred during audio encoding: {e}", spinner)
            return None
        
    @classmethod
    def is_audio_encode_needed(cls, job: VideoSyncJob, spinner: Yaspin | None = None, log_prefix="[FFmpeg]", log_path: str | None = None) -> bool:
        """Determines if audio encoding is needed based on the selected codec and source audio format."""
        try:
            selected_stream: AudioStream = job.dst_streams.get_selected_audio_stream()

            if not selected_stream.codec:
                _message = "Destination audio codec is unknown. Skipping encode."
                cu.try_print_spinner_message(f"{cu.fore.LIGHTYELLOW_EX}{log_prefix} {_message}", spinner)
                cls._try_save_log_content(log_path, _message, is_internal=True)
                return False

            if selected_stream.codec in LOSSY_AUDIO_CODEC_PARAMS.keys():
                _message = f"Encoding not needed. Audio is already in a lossy codec ({selected_stream.codec})."
                cu.try_print_spinner_message(f"{cu.fore.LIGHTBLACK_EX}{log_prefix} {_message}", spinner)
                cls._try_save_log_content(log_path, _message, is_internal=True)
                return False

            return selected_stream.codec in LOSSLESS_AUDIO_CODECS
        except Exception as e:
            _message = f"An error occurred while determining if audio encode is needed: {e}"
            cls._try_save_log_content(log_path, _message, is_internal=True)
            cu.try_print_spinner_message(f"{cu.fore.LIGHTRED_EX}{log_prefix} {_message}", spinner)
            return False
    
    @staticmethod
    def get_pcm_pipe_args(job: VideoSyncJob) -> list[str]:
        """Constructs ffmpeg arguments for piping the selected audio track in pcm format to stdout"""
        return [
            'ffmpeg',
            "-hide_banner",
            "-v", "error",
            '-i', job.dst_filepath,
            '-map', f'0:{job.dst_streams.get_selected_audio_stream().id}',
            "-f", "wav",  # Output format for piping (uncompressed PCM)
            "-"
        ]
