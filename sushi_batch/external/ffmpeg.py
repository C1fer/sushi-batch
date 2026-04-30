import json
import subprocess 

from pathlib import Path

from ..utils import utils
from ..utils import console_utils as cu
from ..external.execution_logger import ExecutionLogger

from ..models import settings as s
from ..models.streams import Stream
from ..models.enums import AudioEncodeCodec, AudioChannelLayout, AudioEncoder
from ..models.job.video_sync_job import VideoSyncJob
from yaspin.core import Yaspin

LIB_KEY = "-c:a"
BITRATE_KEY = "-b:a"

LOSSY_AUDIO_CODEC_OPTIONS = {
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

LOSSLESS_AUDIO_CODECS = {"flac", "pcm", "wav"}

PROBE_CHANNEL_LAYOUT_MAP = {
    "mono": AudioChannelLayout.MONO,
    "stereo": AudioChannelLayout.STEREO,
    "5.1": AudioChannelLayout.SURROUND_5_1,
    "7.1": AudioChannelLayout.SURROUND_7_1,
}

ENCODER_LIB_MAP = {
    AudioEncoder.AAC_FFMPEG: "aac",
    AudioEncoder.EAC3_FFMPEG: "eac3",
    AudioEncoder.LIBOPUS_FFMPEG: "libopus",
}

FALLBACK_ENCODERS = {
    AudioEncoder.XIPH_OPUSENC: AudioEncoder.LIBOPUS_FFMPEG,
}

class FFmpeg:
    is_installed = utils.is_app_installed("ffmpeg")
    is_probe_installed = utils.is_app_installed("ffprobe")
    log_section_name = "Audio Encode (FFmpeg)"

    @classmethod
    def _try_save_log_content(cls, log_path, content, section_name = None, is_internal=False):
        if s.config.general.get("save_merge_logs") and log_path:
            _section_name = section_name or cls.log_section_name
            ExecutionLogger.save_log_output(log_path, content, section_name= _section_name, is_internal=is_internal)

    @classmethod
    def _get_probe_args(cls, filepath, stream_selector=None):
        """Construct ffprobe arguments for extracting stream information."""
        args = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json=compact=1',
            '-show_streams',
            '-show_entries',
            'stream=index,codec_name,codec_type,sample_rate,channel_layout,bits_per_raw_sample,width,height:'
            'stream_tags=title,language:'
            'stream_disposition=default,forced',
            filepath,
        ]
        if stream_selector:
            args.insert(-1, '-select_streams')
            args.insert(-1, stream_selector)

        return args

    @classmethod
    def get_probe_output(cls, filepath, stream_type=None):
        """
        Returns ffprobe output for specified file in JSON format.
        This is used to extract streams information for user selection.
        """
        try:
            if not Path(filepath).is_file():
                raise FileNotFoundError(f"File not found: {filepath}")
            
            args = cls._get_probe_args(filepath, stream_selector=stream_type)
            process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                universal_newlines=True,
                encoding='utf-8',
                errors="ignore"
            )
            output, _ = process.communicate()
            
            return output
        except Exception as e:
            cu.print_error(f"An error occurred while looking for streams in {filepath}: {e}")

    @classmethod 
    def get_clean_probe_info(cls, filepath) -> dict[str, list[dict]]:
        """
        Returns deserialized streams extracted from ffprobe output. Grouped by type.
        """
        try: 
            media_info = cls.get_probe_output(filepath)
            parsed = json.loads(media_info)
            streams_by_type = {}

            for stream in parsed["streams"]:
                codec_type = stream['codec_type']
                
                if codec_type == "attachment":
                    continue

                streams_by_type.setdefault(codec_type, []).append(stream)

            return streams_by_type
        except Exception as e:
            raise Exception("Couldn't parse ffprobe output: {0}".format(str(e)))

    @classmethod 
    def has_subtitles(cls, filepath):
        """Check if specified file contains subtitle streams"""
        try:
            media_info = cls.get_probe_output(filepath, stream_type="s")
            parsed = json.loads(media_info)
            return len(parsed.get("streams", [])) > 0
        except Exception as e:
            cu.print_error(f"An error occurred while checking for subtitles in {filepath}: {e}")
            return False

    @classmethod
    def _get_codec_params(cls, job, settings_codec, settings_encoder):
        ffmpeg_codec_params = LOSSY_AUDIO_CODEC_OPTIONS.get(settings_codec, None)
        if not ffmpeg_codec_params:
            raise ValueError(f"Unsupported audio codec selected for encoding: {settings_codec.name}")
        
        track_layout = job.dst_aud_channel_layout if job.dst_aud_channel_layout else Stream.get_channel_layout_from_display_name(job.dst_aud_display)
        layout_enum = PROBE_CHANNEL_LAYOUT_MAP.get(track_layout, None)
        if not layout_enum:
            cu.print_warning(f"[Job {job.idx} - FFmpeg] Unknown or unsupported channel layout '{track_layout}'. Defaulting to stereo.", nl_before=False, wait=False)
            layout_enum = AudioChannelLayout.STEREO

        selected_bitrate = s.config.merge_workflow["encode_codec_settings"][settings_codec.name]["bitrates"].get(layout_enum.name, None)
        
        ffmpeg_codec_params.update({
            LIB_KEY: ENCODER_LIB_MAP.get(settings_encoder, None),
            BITRATE_KEY: selected_bitrate
        })

        args = []
        for key, value in ffmpeg_codec_params.items():
            args.extend([key, value])
        return args, selected_bitrate
    
    @classmethod
    def _get_audio_encode_args(cls, job: VideoSyncJob, settings_codec: AudioEncodeCodec, settings_encoder: AudioEncoder):
        """Constructs ffmpeg arguments for encoding audio with the selected codec."""
        output_path = f"{job.dst_filepath}_encode.{settings_codec.name.lower()}"
        codec_params, selected_bitrate = cls._get_codec_params(job, settings_codec, settings_encoder)
        
        args = [
            'ffmpeg',
            '-i', job.dst_filepath,
            '-map', f'0:{job.dst_streams.get_selected_audio_stream().id}',
            *codec_params,
            '-y',  # Overwrite output file if it exists
            output_path
        ]
        return args, output_path, selected_bitrate

    @classmethod
    def get_clean_audio_encode_log(cls, content):
        """Returns the clean audio encode log by removing input metadata"""
        try:
            version_info = content.split("Input #0")
            if len(version_info) < 2:
                return content
            output_info = version_info[1].split("Press [q] to stop, [?] for help")
            if len(output_info) < 2:
                return content
            return version_info[0] + output_info[1]
        except Exception:
            return content
    
    @classmethod
    def encode_lossless_audio(cls, job: VideoSyncJob, spinner: Yaspin | None = None, log_prefix="[FFmpeg]", is_fallback=False, log_path: str | None = None) -> str | None:
        """Encodes audio with the selected codec option and saves to *_encode.<ext>."""
        try:
            settings_codec = s.config.merge_workflow.get("encode_codec")
            selected_encoder = s.config.merge_workflow.get("encode_codec_settings", {}).get(settings_codec.name, {}).get("encoder")
            if is_fallback:
                selected_encoder = FALLBACK_ENCODERS.get(selected_encoder, None)

            args, output_path, selected_bitrate = cls._get_audio_encode_args(job, settings_codec, selected_encoder)

            bitrate_display = selected_bitrate.replace('k', ' kbps')
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

            ffmpeg_log = cls.get_clean_audio_encode_log(stderr)
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
            selected_stream = job.dst_streams.get_selected_audio_stream()
            dst_aud_codec = (
                selected_stream.codec.lower()
                if selected_stream.codec
                else ""
            )

            if not dst_aud_codec:
                _message = "Destination audio codec is unknown. Skipping encode."
                cu.try_print_spinner_message(f"{cu.fore.LIGHTYELLOW_EX}{log_prefix} {_message}", spinner)
                cls._try_save_log_content(log_path, _message, is_internal=True)
                return False

            if dst_aud_codec in LOSSY_AUDIO_CODEC_OPTIONS.keys():
                _message = f"Encoding not needed. Audio is already in a lossy codec ({dst_aud_codec})."
                cu.try_print_spinner_message(f"{cu.fore.LIGHTBLACK_EX}{log_prefix} {_message}", spinner)
                cls._try_save_log_content(log_path, _message, is_internal=True)
                return False

            return dst_aud_codec in LOSSLESS_AUDIO_CODECS
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
