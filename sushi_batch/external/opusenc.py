import subprocess

from .ffmpeg import FFmpeg

from ..utils import utils
from ..utils import console_utils as cu

from ..models.enums import AudioEncodeCodec, AudioChannelLayout, AudioEncoder
from ..models import settings as s


class XiphOpusEncoder:
    is_available = utils.is_app_installed("opusenc")
    
    @classmethod
    def encode(cls, job, spinner=None, log_prefix="[Opusenc]"):
        """Encodes audio with opusenc using the codec settings. Pipes audio from ffmpeg and saves to *_encode.opus."""
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

            bitrate_display = layout_bitrate.replace('k', ' kbps')
            out_info = f"Opus ({bitrate_display})"

            if spinner:
                spinner.text = f"{log_prefix} Encoding audio track to {out_info}"
            else:
                cu.print_warning(f"{log_prefix} Encoding audio track to {out_info}", nl_before=False, wait=False)
            
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
            
            cu.try_print_spinner_message(f"{cu.fore.LIGHTGREEN_EX}{log_prefix} Audio track successfully encoded to {out_info}.", spinner)

            job.merge_audio_encode_done = True
            job.merge_audio_encode_codec = AudioEncodeCodec.OPUS.name
            job.merge_audio_encode_encoder = AudioEncoder.XIPH_OPUSENC.name
            job.merge_audio_encode_bitrate = bitrate_display
            return output_path
        except Exception as e:
            cu.try_print_spinner_message(f"{cu.fore.LIGHTRED_EX}{log_prefix} Error encoding with opusenc: {e}", spinner)
