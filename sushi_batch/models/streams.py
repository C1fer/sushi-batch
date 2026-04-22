from ..utils import console_utils as cu
from ..utils import constants


class Stream:
    def __init__(self, track_id, codec, lang, info, title=""):
        self.id = track_id
        self.codec = codec
        self.lang = lang
        self.info = info
        self.title = title
        self.display_name = f"{track_id} - {lang}, {codec}{info}" if title == "" else f"{track_id} - {title}, {codec}, {lang}{info}"

    @classmethod
    def get_audio_streams_from_probe(cls, probed_tracks):
        """Get audio stream objects from FFprobe output"""
        if len(probed_tracks) == 0:
            return []
        
        streams = []
        for track in probed_tracks:
            track_id = track.get('index')
            codec = track.get('codec_name')
            title = track.get('tags', {}).get('title', '')
            lang = track.get('tags', {}).get('language', 'und')
            
            info = ''.join(filter(None, [
                f", {track.get('sample_rate')} Hz" if track.get('sample_rate') else None,
                f", {track.get('channel_layout')}" if track.get('channel_layout') else None,
                f", {track.get('bits_per_raw_sample')} bits" if track.get('bits_per_raw_sample') else None,
                " (forced)" if track.get('disposition', {}).get('forced', 0) == 1 else None,
                " (default)" if track.get('disposition', {}).get('default', 0) == 1 else None
            ]))

            streams.append(Stream(track_id, codec, lang, info, title))
               
        return streams
    
    @classmethod
    def get_sub_streams_from_probe(cls, probed_tracks):
        """Get subtitle stream objects from FFprobe output"""
        if len(probed_tracks) == 0:
            return []

        streams = []
        for track in probed_tracks:
            track_id = track.get('index')
            codec = track.get('codec_name', None)
            title = track.get('tags', {}).get('title', '')
            lang = track.get('tags', {}).get('language', 'und')

            info = ''.join(filter(None, [
                " (forced)" if track.get('disposition', {}).get('forced', 0) == 1 else None,
                " (default)" if track.get('disposition', {}).get('default', 0) == 1 else None
            ]))

            streams.append(Stream(track_id, codec, lang, info, title))
               
        return streams
    
    @staticmethod
    def get_stream_lang(streams, stream_id):
        """Get language code of specified stream"""
        for stream in streams:
            if stream.id == stream_id:
                lang = stream.lang if not stream.lang == "" else "und"
                return lang

    @staticmethod
    def get_stream_name(streams, stream_id):
        """Get title/name of specified stream"""
        for stream in streams:
            if stream.id == stream_id:
                return stream.title
            
    @staticmethod
    def get_subtitle_extension(streams, stream_id):
        """Get subtitle file extension based on stream codec"""
        for stream in streams:
            if stream.id == stream_id:
                return constants.subtitle_codec_extension_map.get(stream.codec, None)