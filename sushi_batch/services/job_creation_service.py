from ..external.ffprobe import FFprobe, ParsedProbeOutput
from ..models.enums import Task
from ..models.job.audio_sync_job import AudioSyncJob
from ..models.job.base_job import JobSync
from ..models.job.video_sync_job import JobMediaStreams, VideoSyncJob
from ..services.stream_service import StreamService
from ..utils import console_utils as cu
from ..utils import constants
from pathlib import Path


class JobCreationService:
    @staticmethod
    def validate_files(src_files: list[str], dst_files: list[str], sub_files: list[str], task: Task) -> bool:
        """Validate selected files / files found in directories fo."""
        src_len: int = len(src_files)
        dst_len: int = len(dst_files)
        sub_len: int = len(sub_files)

        validations: list[tuple[bool, str]] = [
            (src_len == 0, "No source files found!"),
            (dst_len == 0, "No sync target files found!"),
            (src_len != dst_len, f"Source ({src_len}) and sync target ({dst_len}) file counts don't match!"),
            (task in constants.AUDIO_TASKS and src_len != sub_len, f"Audio ({src_len}) and subtitle ({sub_len}) file counts don't match!"),
        ]

        for condition, error_msg in validations:
            if condition:
                cu.print_error(error_msg)
                return False
        return True

    @classmethod
    def _is_video_sync_job_invalid(cls, src_probe_info: ParsedProbeOutput, dst_probe_info: ParsedProbeOutput) -> bool:
        return any([
            len(src_probe_info["audio"]) == 0,
            len(src_probe_info["subtitle"]) == 0,
            len(dst_probe_info["audio"]) == 0
        ])
            
    @classmethod
    def create_video_sync_jobs(cls,src_files: list[str], dst_files: list[str], task: Task) -> list[VideoSyncJob]:
        jobs: list[VideoSyncJob] = []
        for idx, (src_filepath, dst_filepath) in enumerate(zip(src_files, dst_files), start=1):
            src_media_info: ParsedProbeOutput = FFprobe.get_parsed_output(src_filepath)
            dst_media_info: ParsedProbeOutput = FFprobe.get_parsed_output(dst_filepath)
            
            if cls._is_video_sync_job_invalid(src_media_info, dst_media_info):
                continue
            
            jobs.append(
                VideoSyncJob(
                    id=idx,
                    src_filepath=str(Path(src_filepath)) if task == Task.VIDEO_SYNC_FIL else src_filepath, # Path is already normalized for directory search,
                    dst_filepath=str(Path(dst_filepath)) if task == Task.VIDEO_SYNC_FIL else dst_filepath,
                    src_streams=JobMediaStreams(
                        video=[], # Not needed 
                        audio=StreamService.get_audio_streams_from_probe(src_media_info["audio"]),
                        subtitle=StreamService.get_sub_streams_from_probe(src_media_info["subtitle"]),
                    ),
                    dst_streams=JobMediaStreams(
                        video=StreamService.get_video_streams_from_probe(dst_media_info["video"]),
                        audio=StreamService.get_audio_streams_from_probe(dst_media_info["audio"]),
                        subtitle=[], # Not needed
                    ),
                    sync=JobSync(task=task),
                )
            )
        return jobs

    @staticmethod
    def create_audio_sync_jobs(src_files: list[str], dst_files: list[str], sub_files: list[str], task: Task) -> list[AudioSyncJob]:
        """Create audio sync job objects from from source, sync target and subtitle combinations."""
        jobs: list[AudioSyncJob] = []
        for idx, (src_filepath, dst_filepath, sub_filepath) in enumerate(zip(src_files, dst_files, sub_files), start=1):
            jobs.append(
                AudioSyncJob(
                    id=idx,
                    src_filepath=str(Path(src_filepath)) if task == Task.AUDIO_SYNC_FIL else src_filepath, # Path is already normalized for directory search,
                    dst_filepath=str(Path(dst_filepath)) if task == Task.AUDIO_SYNC_FIL else dst_filepath,
                    sub_filepath=str(Path(sub_filepath)) if task == Task.AUDIO_SYNC_FIL else sub_filepath,
                    sync=JobSync(task=task),
                )
            )
        return jobs