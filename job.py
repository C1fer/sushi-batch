class Job:
    def __init__(self, src_file, dst_file, sub_file=None, task=None, aud_track_id=None, sub_track_id=None):
        self.src_file = src_file
        self.dst_file = dst_file
        self.sub_file = sub_file
        self.task = task
        self.aud_track_id = aud_track_id
        self.sub_track_id = sub_track_id
        self.status = "Not Started"
