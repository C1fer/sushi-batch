from copy import deepcopy
from json import JSONDecoder, JSONEncoder

from ...models.enums import AudioEncodeCodec, AudioEncoder, QueueTheme
from ..utils import pop_many


class SettingsEncoder(JSONEncoder):
    def default(self, o):
        from ...models.settings import Settings
        if isinstance(o, Settings):
            dct = deepcopy(o.__dict__)
            dct["general"]["queue_theme"] = o.general.get("queue_theme").name
            dct["merge_workflow"]["encode_codec"] = o.merge_workflow.get("encode_codec").name
            for _, codec_settings in dct["merge_workflow"]["encode_codec_settings"].items():
                codec_settings["encoder"] = codec_settings.get("encoder").name
            return dct
        return super().default(o)    

class SettingsDecoder(JSONDecoder):
    def __init__(self, **kwargs):
        kwargs.setdefault("object_hook", self.object_hook)
        super().__init__(**kwargs)

    def _migrate_merge_src_to_v2(self, dct):
        dct["merge_src_file"] = {
            "copy_attachments": dct.get("src_copy_attachments", True),
            "copy_chapters": dct.get("src_copy_chapters", False),
            "copy_global_tags": dct.get("src_copy_global_tags", False),
            "copy_track_tags": dct.get("src_copy_track_tags", False)
        }
        pop_many(dct, "src_copy_attachments", "src_copy_chapters", "src_copy_global_tags", "src_copy_track_tags")
    
    def _migrate_merge_dst_to_v2(self, dct):
        dct["merge_dst_file"] = {
            "copy_only_selected_sync_audio_track": dct.get("dst_copy_audio_tracks", False),
            "copy_attachments": dct.get("dst_copy_attachments", True),
            "copy_chapters": dct.get("dst_copy_chapters", True),
            "copy_subtitle_tracks": dct.get("dst_copy_subtitle_tracks", True),
            "copy_global_tags": dct.get("dst_copy_global_tags", True),
            "copy_track_tags": dct.get("dst_copy_track_tags", True)
        }
        pop_many(dct, "dst_copy_audio_tracks", "dst_copy_attachments", "dst_copy_chapters", "dst_copy_subtitle_tracks", "dst_copy_global_tags", "dst_copy_track_tags")

    def _migrate_merge_synced_sub_to_v2(self, dct):
        dct["merge_synced_sub_file"] = {
            "default_flag": dct.get("sub_default_flag", True),
            "forced_flag": dct.get("sub_forced_flag", False),
            "custom_trackname": dct.get("sub_custom_trackname", False),
            "trackname": dct.get("sub_trackname", "Synced Sub")
        }
        pop_many(dct, "sub_default_flag", "sub_forced_flag", "sub_custom_trackname", "sub_trackname")

    def _migrate_general_settings_to_v2(self, dct):
        dct["general"] = {
            "queue_theme": QueueTheme[dct.get("queue_theme", "CARD")],
            "save_sushi_logs": dct.get("save_sushi_logs", True),
            "save_merge_logs": dct.get("save_mkvmerge_logs", False)
        }
        pop_many(dct, "queue_theme", "save_sushi_logs", "save_mkvmerge_logs")

    def _migrate_merge_workflow_settings_to_v2(self, dct):
        dct["merge_workflow"] = {
            "merge_files_after_execution": dct.get("merge_files_after_execution", True),
            "resample_subs_on_merge": dct.get("resample_subs_on_merge", False),
            "delete_generated_files_after_merge": dct.get("delete_generated_files_after_merge", False)
        }
        pop_many(dct, "merge_files_after_execution", "resample_subs_on_merge", "delete_generated_files_after_merge")

    def _migrate_sync_workflow_settings_to_v2(self, dct):
        dct["sync_workflow"] = {
            "use_high_quality_resample": dct.get("use_high_quality_resample", True),
            "enable_sushi_advanced_args": dct.get("enable_sushi_advanced_args", False),
            "sushi_advanced_args": {
                "window": dct.get("sushi_window", None),
                "max_window": dct.get("sushi_max_window", None),
                "rewind_thresh": dct.get("sushi_rewind_thresh", None),
                "smooth_radius": dct.get("sushi_smooth_radius", None),
                "max_ts_duration": dct.get("sushi_max_ts_duration", None),
                "max_ts_distance": dct.get("sushi_max_ts_distance", None)
            }
        }
        pop_many(dct, "use_high_quality_resample", "enable_sushi_advanced_args", "sushi_window", "sushi_max_window", "sushi_rewind_thresh", "sushi_smooth_radius", "sushi_max_ts_duration", "sushi_max_ts_distance")


    def _migrate_legacy_to_v2(self, dct):
        """Detects and maps legacy objects to the current structure for backwards compatibility."""
        self._migrate_merge_src_to_v2(dct)
        self._migrate_merge_dst_to_v2(dct)
        self._migrate_merge_synced_sub_to_v2(dct)
        self._migrate_general_settings_to_v2(dct)
        self._migrate_merge_workflow_settings_to_v2(dct)
        self._migrate_sync_workflow_settings_to_v2(dct)

    def object_hook(self, dct):
        if  dct.get("data_path", None) and not dct.get("schema_version", None):
            self._migrate_legacy_to_v2(dct)
            return dct 

        if dct.get("queue_theme", None):
            dct["queue_theme"] = QueueTheme[dct["queue_theme"]]
            return dct

        if dct.get("encode_codec", None):
            dct["encode_codec"] = AudioEncodeCodec[dct["encode_codec"]]
            return dct
        
        if dct.get("encoder", None):
            dct["encoder"] = AudioEncoder[dct["encoder"]]
            return dct
        
        return dct