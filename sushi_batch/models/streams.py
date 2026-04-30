import re


SUBTITLE_CODEC_MAP = {
    "ass": ".ass",
    "subrip": ".srt",
    "ssa": ".ssa"
}
    
class Stream:
    def __init__(
        self,
        track_id=None,
        codec=None,
        lang=None,
        title=None,
        channel_layout=None,
        default=None,
        forced=None,
        display_name=None,
    ):
        self.id = track_id
        self.codec = codec
        self.lang = lang
        self.title = title
        self.channel_layout = channel_layout
        self.default = default
        self.forced = forced
        self.display_name = display_name

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
            channel_layout = track.get('channel_layout', '')
            lang = track.get('tags', {}).get('language', 'und')
            default = track.get('disposition', {}).get('default', 0) == 1
            forced = track.get('disposition', {}).get('forced', 0) == 1

            info = ''.join(filter(None, [
                f", {track.get('sample_rate')} Hz" if track.get('sample_rate') else None,
                f", {channel_layout}" if channel_layout else None,
                f", {track.get('bits_per_raw_sample')} bits" if track.get('bits_per_raw_sample') else None,
                " (forced)" if forced else None,
                " (default)" if default else None
            ]))

            display_name = (
                f"{track_id} - {lang}, {codec}{info}"
                if title == ""
                else f"{track_id} - {title}, {codec}, {lang}{info}"
            )

            streams.append(Stream(
                track_id=track_id, 
                codec=codec, 
                lang=lang, 
                title=title,
                channel_layout=channel_layout,
                default=default,
                forced=forced,
                display_name=display_name,
            ))
               
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
            forced = track.get('disposition', {}).get('forced', 0) == 1
            default = track.get('disposition', {}).get('default', 0) == 1


            info = ''.join(filter(None, [
                " (forced)" if track.get('disposition', {}).get('forced', 0) == 1 else None,
                " (default)" if track.get('disposition', {}).get('default', 0) == 1 else None
            ]))

            display_name = (
                f"{track_id} - {lang}, {codec}{info}"
                if title == ""
                else f"{track_id} - {title}, {codec}, {lang}{info}"
            )

            streams.append(Stream(
                track_id=track_id,
                codec=codec,
                lang=lang,
                title=title,
                default=default,
                forced=forced,
                display_name=display_name,
            ))
               
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
                return SUBTITLE_CODEC_MAP.get(stream.codec, None)
            
    @staticmethod
    def get_codec_from_display_name(display_name):
        """Get codec name from the constructor-built display string."""
        if not display_name:
            return None

        display_name = str(display_name).strip()
        if " - " not in display_name:
            return None

        suffix = display_name.split(" - ", 1)[1]
        parts = [part.strip() for part in suffix.split(", ") if part.strip()]

        if len(parts) >= 2:
            return parts[1]

        match = re.search(r"^.+? - .+?, (?P<codec>[^,]+)(?:,|$)", display_name)
        if match:
            return match.group("codec").strip()

        return None
    
    @staticmethod
    def get_channel_layout_from_display_name(display_name):
        """Get channel layout from the constructor-built display string."""
        if not display_name:
            return None
        
        keys = {"stereo", "5.1", "7.1"}
        return next((key for key in keys if f", {key}" in display_name), None)
