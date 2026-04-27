import json
import subprocess 

from pathlib import Path

from ..utils import utils
from ..utils import console_utils as cu

from ..models import settings as s
from ..models.streams import Stream
from ..models.enums import AudioEncodeCodec, AudioChannelLayout

BITRATE_KEY = "-b:a"

LOSSY_AUDIO_CODEC_OPTIONS = {
    AudioEncodeCodec.OPUS: {
        "-c:a": "libopus",
        BITRATE_KEY: "",
        "-vbr": "on",
        "-compression_level": "10"
    },
    AudioEncodeCodec.AAC: {
        "-c:a": "aac",
        BITRATE_KEY: "",
        "-q:a": "2",
        "-profile:a": "aac_low"
    },
    AudioEncodeCodec.EAC3: {
        "-c:a": "eac3",
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

class FFmpeg:
    is_installed = utils.is_app_installed("ffprobe")

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
    def get_clean_probe_info(cls, filepath):
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
    def _get_codec_params(cls, job, settings_codec):
        ffmpeg_codec_params = LOSSY_AUDIO_CODEC_OPTIONS.get(settings_codec, None)
        if not ffmpeg_codec_params:
            raise ValueError(f"Unsupported audio codec selected for encoding: {settings_codec.name}")
        
        track_layout = job.dst_aud_channel_layout if job.dst_aud_channel_layout else Stream.get_channel_layout_from_display_name(job.dst_aud_display)
        layout_enum = PROBE_CHANNEL_LAYOUT_MAP.get(track_layout, None)
        if not layout_enum:
            cu.print_warning(f"[Job {job.idx} - FFmpeg] Unknown or unsupported channel layout '{track_layout}'. Defaulting to stereo.", nl_before=False, wait=False)
            layout_enum = AudioChannelLayout.STEREO

        selected_bitrate = s.config.merge_workflow.get("encode_audio_bitrates").get(settings_codec.name, {}).get(layout_enum.name, None)

        ffmpeg_codec_params[BITRATE_KEY] = selected_bitrate

        args = []
        for key, value in ffmpeg_codec_params.items():
            args.extend([key, value])
        return args, selected_bitrate
    
    @classmethod
    def _get_audio_encode_args(cls, job, settings_codec):
        """Constructs ffmpeg arguments for encoding audio with the selected codec."""
        output_path = f"{job.dst_file}_encode.{settings_codec.name.lower()}"
        codec_params, selected_bitrate = cls._get_codec_params(job, settings_codec)
        
        args = [
            'ffmpeg',
            '-i', job.dst_file,
            '-map', f'0:{job.dst_aud_id}',
            *codec_params,
            '-y',  # Overwrite output file if it exists
            output_path
        ]
        return args, output_path, selected_bitrate
    
    @classmethod
    def encode_lossless_audio(cls, job):
        """Encodes audio with the selected codec option and saves to *_encode.<ext>."""
        try:
            log_prefix  = f"[Job {job.idx} - FFmpeg]"

            settings_codec = s.config.merge_workflow.get("encode_ffmpeg_codec")
            args, output_path, selected_bitrate = cls._get_audio_encode_args(job, settings_codec)
            cu.print_warning(f"{log_prefix} Encoding audio track to {settings_codec.value} ({selected_bitrate})", nl_before=False, wait=False)
           
            subprocess.run(
                args,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            
            job.merge_audio_encode_done = True
            job.merge_audio_encode_codec = settings_codec.name
            job.merge_audio_encode_bitrate = selected_bitrate
            return output_path
        except Exception as e:
            cu.print_error(f"{log_prefix} An error occurred during audio encoding: {e}")
            return None
        
    @staticmethod
    def is_audio_encode_needed(job):
        """Determines if audio encoding is needed based on the selected codec and source audio format."""
        log_prefix = f"[Job {job.idx} - FFmpeg]"
        
        dst_aud_codec = (
            job.dst_aud_codec.lower()
            if job.dst_aud_codec
            else Stream.get_codec_from_display_name(job.dst_aud_display)
        )

        if not dst_aud_codec:
            cu.print_warning(f"{log_prefix} Destination audio codec is unknown. Skipping audio encoding.", nl_before=False, wait=False)
            return False

        if dst_aud_codec in LOSSY_AUDIO_CODEC_OPTIONS.keys():
            cu.print_warning(f"{log_prefix} Audio encoding not needed. Audio is already in a lossy codec ({dst_aud_codec}).", nl_before=False, wait=False)
            return False
        return dst_aud_codec in LOSSLESS_AUDIO_CODECS