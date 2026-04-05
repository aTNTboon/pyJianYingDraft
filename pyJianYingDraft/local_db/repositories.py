import os
from typing import Iterable

from .core import LocalMediaDatabase
from .models import AudioRecord, MaskRecord, VideoRecord


class MaskRepository:
    def __init__(self, db: LocalMediaDatabase):
        self.db = db

    def upsert_many(self, records: Iterable[MaskRecord]) -> None:
        with self.db.connect() as conn:
            conn.executemany(
                """
                INSERT INTO mask(name, mask_path, ext)
                VALUES (?, ?, ?)
                ON CONFLICT(mask_path) DO UPDATE SET
                    name = excluded.name,
                    ext = excluded.ext
                """,
                [(r.name, r.mask_path, r.ext) for r in records],
            )


class VideoRepository:
    def __init__(self, db: LocalMediaDatabase):
        self.db = db

    def upsert_many(self, records: Iterable[VideoRecord]) -> None:
        with self.db.connect() as conn:
            conn.executemany(
                """
                INSERT INTO video(name, video_path, ext)
                VALUES (?, ?, ?)
                ON CONFLICT(video_path) DO UPDATE SET
                    name = excluded.name,
                    ext = excluded.ext
                """,
                [(r.name, r.video_path, r.ext) for r in records],
            )


class AudioRepository:
    def __init__(self, db: LocalMediaDatabase):
        self.db = db

    def upsert_many(self, records: Iterable[AudioRecord]) -> None:
        with self.db.connect() as conn:
            conn.executemany(
                """
                INSERT INTO audio(name, audio_path, subtitle_path, ext, tags, duration_seconds)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(audio_path) DO UPDATE SET
                    name = excluded.name,
                    subtitle_path = excluded.subtitle_path,
                    ext = excluded.ext,
                    tags = excluded.tags,
                    duration_seconds = excluded.duration_seconds,
                    updated_at = CURRENT_TIMESTAMP
                """,
                [
                    (r.name, r.audio_path, r.subtitle_path, r.ext, r.tags, r.duration_seconds)
                    for r in records
                ],
            )


def scan_media_records(media_dir: str, exts: tuple[str, ...]) -> list[tuple[str, str, str]]:
    if not os.path.exists(media_dir):
        return []
    records = []
    for name in os.listdir(media_dir):
        path = os.path.join(media_dir, name)
        if not os.path.isfile(path):
            continue
        root, ext = os.path.splitext(name)
        if ext.lower() in exts:
            records.append((root, path, ext.lower()))
    return records
