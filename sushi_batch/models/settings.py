import json
from copy import deepcopy
from os import makedirs, path

from ..utils import console_utils as cu
from ..utils.json.settings_json import SettingsDecoder, SettingsEncoder

from .enums import QueueTheme, AudioEncodeCodec, AudioChannelLayout, AudioEncoder


DEFAULT_ENCODE_CODEC_SETTINGS = {
    AudioEncodeCodec.OPUS.name: {
        "encoder": AudioEncoder.LIBOPUS_FFMPEG,
        "bitrates": {
            AudioChannelLayout.MONO.name: "64k",
            AudioChannelLayout.STEREO.name: "128k",
            AudioChannelLayout.SURROUND_5_1.name: "320k",
            AudioChannelLayout.SURROUND_7_1.name: "448k"
        }
    },
    AudioEncodeCodec.AAC.name: {
        "encoder": AudioEncoder.AAC_FFMPEG,
        "bitrates": {
            AudioChannelLayout.MONO.name: "64k",
            AudioChannelLayout.STEREO.name: "192k",
            AudioChannelLayout.SURROUND_5_1.name: "448k",      
            AudioChannelLayout.SURROUND_7_1.name: "640k"      
        }
    },
    AudioEncodeCodec.EAC3.name: {
        "encoder": AudioEncoder.EAC3_FFMPEG,
        "bitrates": {
            AudioChannelLayout.MONO.name: "96k",
            AudioChannelLayout.STEREO.name: "224k",   
            AudioChannelLayout.SURROUND_5_1.name: "448k",     
            AudioChannelLayout.SURROUND_7_1.name: "768k"
        }
    }
}


class Settings():

    def __init__(self):
        # Default paths
        self.schema_version = 2.0
        self.data_path = path.join(path.expanduser('~/Documents'), 'SushiBatchTool')
        self.file_path = path.join(self.data_path, "settings.json")

        # General Settings
        self.general = {
            "queue_theme": QueueTheme.CARD,
            "save_sushi_logs": True,
            "save_merge_logs": True,
        }

        # Sync Workflow Settings
        self.sync_workflow = {
            "use_high_quality_resample": True, # Enables 24kHz resampling for better event search. Increasses processing time but can improve sync accuracy.
            "enable_sushi_advanced_args": False,
            "sushi_advanced_args": {
                "window": None,
                "max_window": None,
                "rewind_thresh": None,
                "smooth_radius": None,
                "max_ts_duration": None,
                "max_ts_distance": None,
            }
        }

        self.merge_workflow = {
            "merge_files_after_execution": True,
            "encode_lossless_audio_before_merging": False,
            "encode_codec": AudioEncodeCodec.OPUS,
            "encode_codec_settings": deepcopy(DEFAULT_ENCODE_CODEC_SETTINGS),
            "resample_subs_on_merge": False,
            "delete_generated_files_after_merge": False,
        }
        
        self.merge_src_file = {
            "copy_attachments": True,
            "copy_chapters": False,
            "copy_global_tags": False,
            "copy_track_tags": False,
        }
        
        self.merge_dst_file = {
            "copy_only_selected_sync_audio_track": False,
            "copy_attachments": True,
            "copy_chapters": True,
            "copy_subtitle_tracks": True,
            "copy_global_tags": True,
            "copy_track_tags": True,
        }

        self.merge_synced_sub_file = {
            "default_flag": True,
            "forced_flag": False,
            "custom_trackname": False,
            "trackname": "Synced Sub",
        }

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
            for key, value in data.items():
                match value:
                    case dict():
                        getattr(self, key).update(value)
                    case _:
                        setattr(self, key, value)
    
    def handle_load(self):
        """Load settings from file or create new file with default settings"""
        if path.exists(self.file_path):
            self._load()
        else:
            makedirs(self.data_path, exist_ok=True)
            self._save()

    def handle_save(self):
        """Save settings to file"""
        self._save()
        
    def restore(self):
        """Restore default settings"""
        self.__init__()
        self._save()
        

# Create Settings instance to allow access in other modules
config = Settings()