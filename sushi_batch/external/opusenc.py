import subprocess

from .ffmpeg import FFmpeg

from ..utils import utils
from ..utils import console_utils as cu
from ..external.execution_logger import ExecutionLogger

from ..models.enums import AudioEncodeCodec, AudioChannelLayout, AudioEncoder
from ..models import settings as s


class XiphOpusEncoder:
    is_available = utils.is_app_installed("opusenc")
    log_section_name = "Audio Encode (Opusenc)"

    @classmethod
    def _try_save_log_content(cls, log_path, content, section_name = None, is_internal=False):
        if s.config.general.get("save_merge_logs") and log_path:
            _section_name = section_name or cls.log_section_name
            ExecutionLogger.save_log_output(log_path, content, section_name= _section_name, is_internal=is_internal)
    
    @classmethod
    def encode(cls, job, spinner=None, log_prefix="[Opusenc]", log_path=None):
        """Encodes audio with opusenc using the codec settings. Pipes decoded audio from FFmpeg to opusenc and saves to *_encode.opus."""
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

            ffmpeg_log = ffmpeg_pipe_process.stderr.read()
            if ffmpeg_log:
                ffmpeg_log += "\n"

            # Close pipes when opusenc exits
            ffmpeg_pipe_process.stdout.close()  
            ffmpeg_pipe_process.stderr.close()

            _, opusenc_stderr = encode_process.communicate()

            opusenc_log = f"{ExecutionLogger.internal_log_indicator}Running with arguments: {(' '.join(encode_args))}\n\n{opusenc_stderr}"

            cls._try_save_log_content(log_path, opusenc_log)

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
