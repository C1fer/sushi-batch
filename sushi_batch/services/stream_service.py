from ..models.stream import AudioStream, SubtitleStream, VideoStream

SUBTITLE_CODEC_MAP: dict[str, str] = {
    "ass": ".ass",
    "subrip": ".srt",
    "ssa": ".ssa"
}


class StreamService:
    @staticmethod
    def get_audio_streams_from_probe(probed_tracks) -> list[AudioStream]:
        """Get audio stream objects from FFprobe output"""
        if len(probed_tracks) == 0:
            return []

        streams: list[AudioStream] = []

        for track in probed_tracks:
            new_stream = AudioStream(
                id=track.get('index'),
                codec=track.get('codec_name'),
                title=track.get('tags', {}).get('title', ''),
                channel_layout=track.get('channel_layout', ''),
                lang=track.get('tags', {}).get('language', 'und'),
                default=track.get('disposition', {}).get('default', 0) == 1,
                forced=track.get('disposition', {}).get('forced', 0) == 1,
                selected=False,
                display_label="",
            )

            info = ''.join(filter(None, [
                f", {track.get('sample_rate')} Hz" if track.get('sample_rate') else None,
                f", {new_stream.channel_layout}" if new_stream.channel_layout else None,
                f", {track.get('bits_per_raw_sample')} bits" if track.get('bits_per_raw_sample') else None,
                " (forced)" if new_stream.forced else None,
                " (default)" if new_stream.default else None
            ]))

            new_stream.display_label = (
                f"{new_stream.id} - {new_stream.lang}, {new_stream.codec}{info}"
                if new_stream.title == ""
                else f"{new_stream.id} - {new_stream.title}, {new_stream.codec}, {new_stream.lang}{info}"
            )
            streams.append(new_stream)

        return streams

    @staticmethod
    def get_sub_streams_from_probe(probed_tracks) -> list[SubtitleStream]:
        """Get subtitle stream objects from FFprobe output"""
        if len(probed_tracks) == 0:
            return []

        streams: list[SubtitleStream] = []
        for track in probed_tracks:
            new_stream = SubtitleStream(
                id=track.get('index'),
                codec=track.get('codec_name', None),
                title=track.get('tags', {}).get('title', ''),
                lang=track.get('tags', {}).get('language', 'und'),
                default=track.get('disposition', {}).get('default', 0) == 1,
                forced=track.get('disposition', {}).get('forced', 0) == 1,
                selected=False,
                extension=SUBTITLE_CODEC_MAP.get(track.get('codec_name', None), None),
                display_label="",
            )
            
            info = ''.join(filter(None, [
                " (forced)" if new_stream.forced else None,
                " (default)" if new_stream.default else None
            ]))

            new_stream.display_label = (
                f"{new_stream.id} - {new_stream.lang}, {new_stream.codec}{info}"
                if new_stream.title == ""
                else f"{new_stream.id} - {new_stream.title}, {new_stream.codec}, {new_stream.lang}{info}"
            )

            streams.append(new_stream)
               
        return streams

    @staticmethod
    def get_video_streams_from_probe(probed_tracks) -> list[VideoStream]:
        """Get video stream objects from FFprobe output"""
        if len(probed_tracks) == 0:
            return []

        return [
            VideoStream(
                id=track.get("index"),
                width=track.get("width"),
                height=track.get("height"),
            )
            for track in probed_tracks
        ]