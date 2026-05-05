import subprocess
from pathlib import Path

from yaspin.core import Yaspin

from ..external.execution_logger import ExecutionLogger
from ..models import settings as s
from ..models.enums import AudioChannelLayout, AudioEncodeCodec, AudioEncoder
from ..models.job.video_sync_job import VideoSyncJob
from ..models.stream import AudioStream
from ..utils import console_utils as cu
from ..utils import utils
from ..utils.constants import FFPROBE_CHANNEL_LAYOUT_MAP

LIB_KEY: str = "-c:a"
BITRATE_KEY: str = "-b:a"

LOSSY_AUDIO_CODEC_PARAMS: dict[AudioEncodeCodec, dict[str, str]] = {
    AudioEncodeCodec.OPUS: { # Approximated to opusenc default params
        LIB_KEY: "",
        BITRATE_KEY: "",
        "-vbr": "on",
        "-af": "asetpts=N/SR/TB", # Ensure proper timestamp handling
        "-compression_level": "10",
        "-application": "audio",
        "-frame_duration": "20",
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

ENCODER_LIB_MAP: dict[AudioEncoder, str]  = {
    AudioEncoder.AAC_FFMPEG: "aac",
    AudioEncoder.EAC3_FFMPEG: "eac3",
    AudioEncoder.LIBOPUS_FFMPEG: "libopus",
}

FALLBACK_ENCODERS: dict[AudioEncoder, AudioEncoder] = { AudioEncoder.XIPH_OPUSENC: AudioEncoder.LIBOPUS_FFMPEG }

class FFmpeg:
    is_installed: bool = utils.is_app_installed("ffmpeg")
    log_section_name = "Audio Encode (FFmpeg)"
    version_info: str = ""

    @classmethod
    def _try_save_log_content(
        cls,
        log_path: str | None,
        content: str,
        section_name: str | None = None,
        is_internal: bool = False,
    ):
        if s.config.general["save_merge_logs"] and log_path:
            _section_name: str = section_name or cls.log_section_name
            ExecutionLogger.save_log_output(log_path, content, section_name= _section_name, is_internal=is_internal)
    
    @classmethod
    def _apply_libopus_surround_correction(cls, ffmpeg_codec_params: dict[str, str], layout_enum: AudioChannelLayout) -> None:
        """Normalizes surround audio layout for libopus encoding."""
        ffmpeg_codec_params["-mapping_family"] = "1"
        desired_layout = "5.1" if layout_enum == AudioChannelLayout.SURROUND_5_1 else "7.1"
        layout_filter = f"aformat=channel_layouts={desired_layout}"
        
        existing_filter = ffmpeg_codec_params.get("-af")
        ffmpeg_codec_params["-af"] = f"{existing_filter},{layout_filter}" if existing_filter else layout_filter

    @classmethod
    def _get_codec_params(
        cls,
        stream: AudioStream,
        settings_codec: AudioEncodeCodec,
        settings_encoder: AudioEncoder,
        log_prefix: str,
    ) -> tuple[list[str], str]:
        """Constructs ffmpeg parameters for encoding audio with the selected codec."""
        ffmpeg_codec_params: dict[str, str] = dict(LOSSY_AUDIO_CODEC_PARAMS.get(settings_codec, {}))
        if not ffmpeg_codec_params:
            raise ValueError(f"Unsupported audio codec selected for encoding: {settings_codec.name}")

        track_layout: str = stream.channel_layout
        layout_enum: AudioChannelLayout | None = next(
            (
                layout
                for layout in FFPROBE_CHANNEL_LAYOUT_MAP.keys()
                if track_layout in FFPROBE_CHANNEL_LAYOUT_MAP[layout]
            ),
            None,
        )
        if not layout_enum:
            cu.print_warning(f"{log_prefix} Unknown or unsupported channel layout '{track_layout}'. Defaulting to stereo.", nl_before=False, wait=False)
            layout_enum = AudioChannelLayout.STEREO

        selected_bitrate: str | None = s.config.merge_workflow["encode_codec_settings"][settings_codec.name]["bitrates"].get(layout_enum.name)
        encoder_lib: str | None = ENCODER_LIB_MAP.get(settings_encoder)
        if not encoder_lib:
            raise ValueError(f"No FFmpeg library mapping for encoder: {settings_encoder.name}")
        if not selected_bitrate:
            raise ValueError(f"No bitrate configured for {settings_codec.name} / layout {layout_enum.name}")

        if settings_codec == AudioEncodeCodec.OPUS and layout_enum in { AudioChannelLayout.SURROUND_5_1,AudioChannelLayout.SURROUND_7_1 }:
          cls._apply_libopus_surround_correction(ffmpeg_codec_params, layout_enum)

        ffmpeg_codec_params.update({LIB_KEY: encoder_lib, BITRATE_KEY: selected_bitrate})

        args: list[str] = []
        for key, value in ffmpeg_codec_params.items():
            args.extend([key, value])
        return args, selected_bitrate
    
    @classmethod
    def _get_audio_encode_args(
        cls,
        input_filepath: str,
        stream: AudioStream,
        settings_codec: AudioEncodeCodec,
        settings_encoder: AudioEncoder,
        log_prefix: str,
    ) -> tuple[list[str], str, str]:
        """Constructs ffmpeg arguments for encoding audio with the selected codec."""
        output_path: str = f"{input_filepath}_track{stream.id}_encode.mka"
        codec_params, selected_bitrate = cls._get_codec_params(stream, settings_codec, settings_encoder, log_prefix)
        
        args: list[str] = [
            'ffmpeg', 
            '-hide_banner',
            '-i', input_filepath,
            '-map', f'0:{stream.id}',
            *codec_params,
            '-y',  # Overwrite output file if it exists
            output_path
        ]
        return args, output_path, selected_bitrate

    @classmethod
    def set_version_info(cls) -> None:
        """Sets the version information of the ffmpeg executable."""
        try:
            version_info: subprocess.CompletedProcess[str] = subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace")
            if version_info.returncode != 0:
                return
            cls.version_info = version_info.stdout.split("\nExiting with exit code")[0]
        except Exception:
            cls.version_info = ""

    @classmethod
    def get_clean_audio_encode_log(cls, content: str, version_info: str | None) -> str:
        """Returns the clean audio encode log by removing input metadata and adding version information"""
        try:
            _version_info: str = version_info or ""
            output_info: list[str] = content.split("Press [q] to stop, [?] for help")
            if len(output_info) < 2:
                return _version_info + content
            return _version_info + output_info[-1]
        except Exception:
            return _version_info + content

    @classmethod
    def encode_lossless_audio(
        cls,
        job: VideoSyncJob,
        stream: AudioStream,
        spinner: Yaspin | None = None,
        log_prefix="[FFmpeg]",
        is_fallback: bool = False,
        log_path: str | None = None,
        log_version_info: bool = True,
    ) -> str | None:
        """Encodes audio with the selected codec option and saves to *_encode.<ext>."""
        track_info: str = f"ID {stream.id}: {stream.title} ({stream.channel_layout})" if not stream.title.isspace() else f"ID {stream.id} ({stream.channel_layout})"
        try:
            settings_codec: AudioEncodeCodec = s.config.merge_workflow["encode_codec"]
            selected_encoder: AudioEncoder = s.config.merge_workflow["encode_codec_settings"][settings_codec.name]["encoder"]

            if is_fallback:
                selected_encoder: AudioEncoder | None = FALLBACK_ENCODERS.get(selected_encoder)
                if not selected_encoder:
                    raise ValueError(f"No fallback encoder found for {settings_codec.name}")

            args, output_path, selected_bitrate = cls._get_audio_encode_args(
                job.dst_filepath,
                stream,
                settings_codec,
                selected_encoder,
                log_prefix,
            )

            bitrate_display: str = selected_bitrate.replace('k', ' kbps')
            out_info = f"{settings_codec.value} ({bitrate_display})"
            
            displayed_message: str = f"Encoding audio track {track_info} to {out_info}"
            if spinner:
                spinner.text = f"{log_prefix} {displayed_message}"
            else:
                cu.print_warning(f"{log_prefix} {displayed_message}", nl_before=False, wait=False)

            if log_version_info and cls.version_info == "": # Only set version info if it hasn't been set yet
                cls.set_version_info()
           
            ffmpeg_encode = subprocess.Popen(
                args,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            _, stderr = ffmpeg_encode.communicate()

            ffmpeg_log: str = cls.get_clean_audio_encode_log(stderr, cls.version_info if log_version_info else None)
            args_log = f"{ExecutionLogger.internal_log_indicator}Running with arguments: {(' '.join(args))}\n\n"
            cls._try_save_log_content(log_path, args_log + ffmpeg_log)

            if ffmpeg_encode.returncode != 0:
                return None

            cu.try_print_spinner_message(f"{cu.fore.LIGHTGREEN_EX}{log_prefix} Track {track_info} successfully encoded to {out_info}.", spinner)
           
            stream.encoded = True
            stream.encode_path = output_path
            stream.encode_bitrate = bitrate_display

            job.merge.audio_encode_done = True
            job.merge.audio_encode_codec = settings_codec.name
            job.merge.audio_encode_encoder = selected_encoder.name
           
            return output_path
        except Exception as e:
            _message: str = f"An error occurred while encoding audio track {track_info}: {e}"
            cls._try_save_log_content(content=_message, log_path=log_path, section_name=cls.log_section_name)
            cu.try_print_spinner_message(f"{cu.fore.LIGHTRED_EX}{log_prefix} {_message}", spinner)
            return None
        
    @classmethod
    def is_audio_encode_needed(
        cls,
        stream: AudioStream,
        spinner: Yaspin | None = None,
        log_prefix="[FFmpeg]",
        log_path: str | None = None,
        is_new_encoder_for_job: bool = False,
    ) -> bool:
        """Determines if audio encoding is needed based on the selected codec and source audio format."""
        try:
            if stream.encoded and stream.encode_path and Path(stream.encode_path).is_file() and not is_new_encoder_for_job:
                _message = f"Audio track {stream.display_label} is already encoded at {stream.encode_path}."
                cu.try_print_spinner_message(f"{cu.fore.LIGHTBLACK_EX}{log_prefix} {_message}", spinner)
                cls._try_save_log_content(log_path, _message, is_internal=True)
                return False

            if not stream.codec:
                _message = f"Destination audio codec is unknown. Skipping encode for track {stream.display_label}."
                cu.try_print_spinner_message(f"{cu.fore.LIGHTYELLOW_EX}{log_prefix} {_message}", spinner)
                cls._try_save_log_content(log_path, _message, is_internal=True)
                return False

            if stream.codec in LOSSY_AUDIO_CODEC_PARAMS.keys():
                _message = f"Encoding not needed. Audio is already in a lossy codec ({stream.display_label}: {stream.codec})."
                cu.try_print_spinner_message(f"{cu.fore.LIGHTBLACK_EX}{log_prefix} {_message}", spinner)
                cls._try_save_log_content(log_path, _message, is_internal=True)
                return False

            return stream.codec in LOSSLESS_AUDIO_CODECS
        except Exception as e:
            _message = f"An error occurred while determining if audio encode is needed for track {stream.display_label}: {e}"
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
            "-" # Pipe to stdout
        ]
