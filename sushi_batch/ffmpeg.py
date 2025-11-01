import subprocess 

from . import utils


class FFmpeg:
    is_installed = utils.is_app_installed("ffmpeg")

    @staticmethod
    def get_probe_output(filepath):
        process = subprocess.Popen(
            ["ffmpeg", "-hide_banner", "-i", filepath],
            stderr=subprocess.PIPE,  # Pipe output to stderr to avoid collision with spinner in stdout
            universal_newlines=True,
            encoding='utf-8',
            errors="ignore"
        )
        _, err = process.communicate()
        
        return err
