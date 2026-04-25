import json
from os import makedirs, path

from ..utils import console_utils as cu
from ..utils.json_utils import SettingsDecoder, SettingsEncoder

from .enums import QueueTheme, AudioEncodeCodec

class Settings():

    def __init__(self):
        # Default paths
        self.data_path = path.join(path.expanduser('~/Documents'), 'SushiBatchTool')
        self.file_path = path.join(self.data_path, "settings.json")

        # General Settings
        self.queue_theme = QueueTheme.CARD
        self.save_sushi_logs = True
        self.save_aegisub_resample_logs = False
        self.save_mkvmerge_logs = False

        # Sync Workflow Settings
        self.use_high_quality_resample = True # Enables 24kHz resampling for better event search. Increasses processing time but can improve sync accuracy.

        # Advanced Sushi Sync Settings 
        self.enable_sushi_advanced_args = False
        self.sushi_window = None
        self.sushi_max_window = None
        self.sushi_rewind_thresh = None
        self.sushi_smooth_radius = None
        self.sushi_max_ts_duration = None
        self.sushi_max_ts_distance = None

        # Merge Workflow Settings
        self.merge_files_after_execution = True
        self.encode_lossless_audio_before_merging = False
        self.encode_ffmpeg_codec = AudioEncodeCodec.OPUS
        self.resample_subs_on_merge = False
        self.delete_generated_files_after_merge = False
        
        # Merge Source File Settings
        self.src_copy_attachments = True
        self.src_copy_chapters = False
        self.src_copy_global_tags = False
        self.src_copy_track_tags = False

        # Merge Sync Target File Settings
        self.dst_copy_audio_tracks = False
        self.dst_copy_attachments = True
        self.dst_copy_chapters = True
        self.dst_copy_subtitle_tracks = True
        self.dst_copy_global_tags = True
        self.dst_copy_track_tags = True

        # Merge Synced Subtitle Settings
        self.sub_default_flag = True
        self.sub_forced_flag = False
        self.sub_custom_trackname = False
        self.sub_trackname = "Synced Sub"

    def _save(self):
        """Save settings to JSON file"""
        try: 
            converted_json = json.dumps(self, indent=4, cls=SettingsEncoder)
            with open(self.file_path, "w", encoding="utf-8") as settings_file:
                settings_file.write(converted_json)
        except Exception as e:
            cu.print_error(f"Error saving settings: {e}", True)

    def _load(self):
        """Load settings from JSON file"""
        with open(self.file_path, "r", encoding="utf-8") as settings_file:
            data = json.load(settings_file, cls=SettingsDecoder)
        # Update instance attributes with loaded settings
        for key, value in data.items():
                setattr(self, key, value)
    
    def handle_load(self):
        """Load settings from file or create new file with default settings"""
        if path.exists(self.file_path):
            self._load()
        else:
            makedirs(self.data_path, exist_ok=True)
            self._save()
        
    def restore(self):
        """Restore default settings"""
        self.__init__()
        self._save()
        

# Create Settings instance to allow access in other modules
config = Settings()