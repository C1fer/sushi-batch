import json
import subprocess 

from pathlib import Path

from ..utils import utils
from ..utils import console_utils as cu
from ..models import settings as s
from ..models.streams import Stream

LOSSY_AUDIO_CODEC_OPTIONS = {
    "opus": "libopus",
    "mp3": "libmp3lame",
    "aac": "aac",
    "eac3": "eac3",
}

LOSSLESS_AUDIO_CODECS = {"flac", "pcm", "wav"}

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
    def _get_audio_encode_args(cls, job, settings_codec):
        """Constructs ffmpeg arguments for encoding audio with the selected codec."""
        ffmpeg_codec = LOSSY_AUDIO_CODEC_OPTIONS.get(settings_codec, None)
        if not ffmpeg_codec:
            raise ValueError(f"Unsupported audio codec selected for encoding: {settings_codec}")
        
        input_file = Path(job.dst_file)
        output_path = str(input_file.with_name(f"{input_file.stem}_encode.{settings_codec}"))

        args = [
            'ffmpeg',
            '-i', job.dst_file,
            '-map', f'0:{job.dst_aud_id}',
            '-c:a', ffmpeg_codec,
            '-y',  # Overwrite output file if it exists
            output_path
        ]
        return args, output_path, ffmpeg_codec
    
    @classmethod
    def encode_lossless_audio(cls, job):
        """Encodes audio with the selected codec option and saves to *_encode.<ext>."""
        try:
            log_prefix  = f"[Job {job.idx} - FFmpeg]"

            settings_codec = s.config.encode_ffmpeg_codec.value
            args, output_path, codec = cls._get_audio_encode_args(job, settings_codec)
            cu.print_warning(f"{log_prefix} Encoding audio track using {codec}", nl_before=False, wait=False)
           
            subprocess.run(
                args,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            
            job.merge_audio_encode_done = True
            job.merge_audio_encode_codec = codec
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