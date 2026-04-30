from ..external.ffmpeg import FFmpeg
from ..models.enums import Task
from ..models.job.video_sync_job import VideoSyncJob, JobMediaStreams
from ..services.stream_service import StreamService
from ..models.job.base_job import JobSync
from ..models.job.audio_sync_job import AudioSyncJob

class JobCreationService:
    @staticmethod
    def _can_create_video_sync_job(src_probe_info: dict, dst_probe_info: dict) -> bool:
        return any([
            len(src_probe_info.get("audio", [])) == 0,
            len(src_probe_info.get("subtitle", [])) == 0,
            len(dst_probe_info.get("audio", [])) == 0,
        ])
            

    @classmethod
    def create_video_sync_jobs(cls,src_files: list[str], dst_files: list[str], task: Task) -> list[VideoSyncJob]:
        jobs: list[VideoSyncJob] = []
        for idx, (src_filepath, dst_filepath) in enumerate(zip(src_files, dst_files), start=1):
            src_media_info = FFmpeg.get_clean_probe_info(src_filepath)
            dst_media_info = FFmpeg.get_clean_probe_info(dst_filepath)
            
            if not cls._can_create_video_sync_job(src_media_info, dst_media_info):
                continue
            
            jobs.append(
                VideoSyncJob(
                    id=idx,
                    src_filepath=src_filepath,
                    dst_filepath=dst_filepath,
                    src_streams=JobMediaStreams(
                        video=StreamService.get_video_streams_from_probe(src_media_info.get("video", [])),
                        audio=StreamService.get_audio_streams_from_probe(src_media_info.get("audio", [])),
                        subtitle=StreamService.get_sub_streams_from_probe(src_media_info.get("subtitle", [])),
                    ),
                    dst_streams=JobMediaStreams(
                        video=StreamService.get_video_streams_from_probe(dst_media_info.get("video", [])),
                        audio=StreamService.get_audio_streams_from_probe(dst_media_info.get("audio", [])),
                        subtitle=StreamService.get_sub_streams_from_probe(dst_media_info.get("subtitle", [])),
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
                    src_filepath=src_filepath,
                    dst_filepath=dst_filepath,
                    sub_filepath=sub_filepath,
                    sync=JobSync(task=task),
                )
            )
        return jobs