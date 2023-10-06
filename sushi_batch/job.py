from .enums import Status, Task


class Job:
    def __init__(
        self,
        idx,
        src_file,
        dst_file,
        sub_file=None,
        task=None,
        src_aud_id=None,
        dst_aud_id=None,
        src_sub_id=None,
        src_sub_lang=None,
        src_sub_name=None,
        status=Status.PENDING,
        result=None,
        merged=None
    ):
        self.idx = idx
        self.src_file = src_file
        self.dst_file = dst_file
        self.sub_file = sub_file
        self.task = task
        self.src_aud_id = src_aud_id
        self.dst_aud_id = dst_aud_id
        self.src_sub_id = src_sub_id
        self.src_sub_lang = src_sub_lang
        self.src_sub_name = src_sub_name
        self.status = status
        self.result = result
        self.merged = merged
