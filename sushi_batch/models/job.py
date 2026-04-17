from pathlib import Path

from .enums import Status


class Job:
    def __init__(
        self,
        idx,
        src_file,
        dst_file,
        sub_file=None,
        task=None,
        src_aud_id=None,
        src_aud_display=None,
        dst_aud_id=None,
        dst_aud_display=None,
        src_sub_id=None,
        src_sub_display=None,
        src_sub_lang=None,
        src_sub_name=None,
        src_sub_ext = None,
        dst_vid_width=None,
        dst_vid_height=None,
        status=Status.PENDING,
        result=None,
        merged=None,
        merged_file=None,
        resample_done=None,
    ):
        self.idx = idx
        self.src_file = self._normalize_path(src_file)
        self.src_aud_id = src_aud_id
        self.src_aud_display = src_aud_display
        self.src_sub_id = src_sub_id
        self.src_sub_display = src_sub_display
        self.src_sub_lang = src_sub_lang
        self.src_sub_name = src_sub_name
        self.src_sub_ext = src_sub_ext

        self.dst_file = self._normalize_path(dst_file)
        self.dst_aud_id = dst_aud_id
        self.dst_aud_display = dst_aud_display
        self.dst_vid_width = dst_vid_width
        self.dst_vid_height = dst_vid_height
        self.sub_file = self._normalize_path(sub_file)
        
        self.task = task
        self.status = status
        self.result = result
        self.merged = merged
        self.merged_file = self._normalize_path(merged_file)
        self.resample_done = resample_done


    @staticmethod
    def _normalize_path(file_path):
        """Normalize path formatting while preserving None values."""
        if file_path is None:
            return None
        return str(Path(file_path))
       