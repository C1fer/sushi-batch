from enums import Status


class Job:
    def __init__(
        self,
        idx,
        src_file,
        dst_file,
        sub_file=None,
        task=None,
        src_aud_track_id=None,
        dst_aud_track_id=None,
        src_sub_track_id=None,
        src_sub_lang=None,
        status=Status.PENDING,
        result=None,
    ):
        self.idx = idx
        self.src_file = src_file
        self.dst_file = dst_file
        self.sub_file = sub_file
        self.task = task
        self.src_aud_track_id = src_aud_track_id
        self.dst_aud_track_id = dst_aud_track_id
        self.src_sub_track_id = src_sub_track_id
        self.src_sub_lang = src_sub_lang
        self.status = status
        self.result = result
