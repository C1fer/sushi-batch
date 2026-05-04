from ..external.ffprobe import ProbeTrack
from ..utils import console_utils as cu
from ..models.stream import AudioStream, SubtitleStream, VideoStream


SUBTITLE_CODEC_MAP: dict[str, str] = {
    "ass": ".ass",
    "subrip": ".srt",
    "ssa": ".ssa"
}

class StreamService:
    @staticmethod
    def get_audio_streams_from_probe(probed_tracks: list[ProbeTrack]) -> list[AudioStream]:
        """Creates audio stream objects from FFprobe output"""
        if len(probed_tracks) == 0:
            return []

        streams: list[AudioStream] = []

        for track in probed_tracks:
            new_stream = AudioStream(
                id=track.get('index'),
                codec=track.get('codec_name'),
                title=track.get('tags').get('title') or '',
                channel_layout=track.get('channel_layout') or '',
                lang=track.get('tags').get('language') or 'und',
                default=track.get('disposition').get('default') == 1,
                forced=track.get('disposition').get('forced') == 1,
                selected=False,
                display_label="",
            )

            info: str = ''.join(filter(None, [
                f", {track.get('sample_rate')} Hz" if track.get('sample_rate') else None,
                f", {new_stream.channel_layout}" if new_stream.channel_layout else None,
                f", {track.get('bits_per_raw_sample')} bits" if track.get('bits_per_raw_sample') else None,
                " (forced)" if new_stream.forced else None,
                " (default)" if new_stream.default else None
            ]))

            new_stream.display_label: str = (
                f"{new_stream.id} - {new_stream.lang}, {new_stream.codec}{info}"
                if new_stream.title == ""
                else f"{new_stream.id} - {new_stream.title}, {new_stream.codec}, {new_stream.lang}{info}"
            )
            streams.append(new_stream)

        return streams

    @staticmethod
    def get_sub_streams_from_probe(probed_tracks: list[ProbeTrack]) -> list[SubtitleStream]:
        """Creates subtitle stream objects from FFprobe output"""
        if len(probed_tracks) == 0:
            return []

        streams: list[SubtitleStream] = []
        for track in probed_tracks:
            codec_name: str = track.get('codec_name') or ''
            extension: str | None = SUBTITLE_CODEC_MAP.get(codec_name, None)

            if not extension:
                cu.print_warning(f"[FFprobe] Unsupported subtitle codec: {codec_name}. Skipping...", nl_before=False, wait=False)
                continue

            new_stream = SubtitleStream(
                id=track.get('index'),
                codec=codec_name,
                title=track.get('tags').get('title') or '',
                lang=track.get('tags').get('language') or 'und',
                default=track.get('disposition').get('default') == 1,
                forced=track.get('disposition').get('forced') == 1,
                selected=False,
                extension=extension,
                display_label="",
            )
            
            info: str = ''.join(filter(None, [
                " (forced)" if new_stream.forced else None,
                " (default)" if new_stream.default else None
            ]))

            new_stream.display_label: str = (
                f"{new_stream.id} - {new_stream.lang}, {new_stream.codec}{info}"
                if new_stream.title == ""
                else f"{new_stream.id} - {new_stream.title}, {new_stream.codec}, {new_stream.lang}{info}"
            )

            streams.append(new_stream)
               
        return streams

    @staticmethod
    def get_video_streams_from_probe(probed_tracks: list[ProbeTrack]) -> list[VideoStream]:
        """Creates video stream objects from FFprobe output"""
        if len(probed_tracks) == 0:
            return []

        return [
            VideoStream(
                id=track.get('index'),
                width=track.get('width') or -1,
                height=track.get('height') or -1,
                default=track.get('disposition').get('default') == 1,
            )
            for track in probed_tracks
        ]