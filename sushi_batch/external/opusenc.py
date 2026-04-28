import subprocess

from .ffmpeg import FFmpeg

from ..utils import utils
from ..utils import console_utils as cu

from ..models.enums import AudioEncodeCodec, AudioChannelLayout
from ..models import settings as s


class XiphOpusEncoder:
    is_available = utils.is_app_installed("opusenc")
    
    @classmethod
    def encode(cls, job):
        """Encodes audio with opusenc using the codec settings. Pipes audio from ffmpeg and saves to *_encode.opus."""
        log_prefix = f"[Job {job.idx} - Opusenc]"
        try:
            layout_bitrate = s.config.merge_workflow["encode_codec_settings"][AudioEncodeCodec.OPUS.name]["bitrates"].get(AudioChannelLayout.STEREO.name, None)
            output_path = f"{job.dst_file}_encode.opus"
            
            encode_args =  [
                "opusenc",
                "--bitrate", layout_bitrate.replace("k", ""),
                "--vbr",
                "-",
                output_path
            ]

            cu.print_warning(f"{log_prefix} Encoding audio track to Opus ({layout_bitrate} kbps)", nl_before=False, wait=False)
            
            ffmpeg_pipe_process = subprocess.Popen(FFmpeg.get_pcm_pipe_args(job), stdout=subprocess.PIPE)

            encode_process = subprocess.Popen(
                encode_args,
                stdin=ffmpeg_pipe_process.stdout,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            ffmpeg_pipe_process.stdout.close()  # Allow ffmpeg to receive a SIGPIPE if opusenc exits
            _, err = encode_process.communicate() 

            if encode_process.returncode != 0:
                return None
            
            job.merge_audio_encode_done = True
            job.merge_audio_encode_codec = AudioEncodeCodec.OPUS.name
            job.merge_audio_encode_bitrate = layout_bitrate
            return output_path
            
        except Exception as e:
            cu.print_error(f"{log_prefix} Error encoding with opusenc: {e}")
