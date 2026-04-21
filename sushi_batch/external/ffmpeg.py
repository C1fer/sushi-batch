import json
import subprocess 

from pathlib import Path

from ..utils import utils
from ..utils import console_utils as cu

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