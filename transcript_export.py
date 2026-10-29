"""Export helpers for file STT transcripts (.srt only)."""
from __future__ import annotations

from pathlib import Path

ALLOWED_EXTENSIONS = {'.mp4', '.mp3', '.m4a', '.wav', '.mkv'}


def is_supported_media(path) -> bool:
    return Path(path).suffix.lower() in ALLOWED_EXTENSIONS


def format_srt_timestamp(seconds: float) -> str:
    if seconds < 0:
        seconds = 0.0
    total_ms = int(round(seconds * 1000))
    hours, rem = divmod(total_ms, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    secs, ms = divmod(rem, 1000)
    return f'{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}'


def segments_to_srt(segments) -> str:
    blocks = []
    index = 1
    for segment in segments:
        if isinstance(segment, dict):
            start = float(segment.get('start', 0))
            end = float(segment.get('end', start))
            text = (segment.get('text') or '').strip()
        else:
            start = float(getattr(segment, 'start', 0) or 0)
            end = float(getattr(segment, 'end', start) or start)
            text = (getattr(segment, 'text', '') or '').strip()
        if not text:
            continue
        if end < start:
            end = start
        blocks.append(
            f'{index}\n'
            f'{format_srt_timestamp(start)} --> {format_srt_timestamp(end)}\n'
            f'{text}\n'
        )
        index += 1
    return '\n'.join(blocks).rstrip() + ('\n' if blocks else '')


def write_srt(media_path, segments) -> Path:
    media = Path(media_path)
    srt_path = media.with_suffix('.srt')
    srt_path.write_text(segments_to_srt(segments), encoding='utf-8')
    return srt_path
