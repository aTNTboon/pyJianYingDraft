import os

from .core import LocalMediaDatabase
from .models import AudioRecord, MaskRecord, VideoRecord
from .repositories import AudioRepository, MaskRepository, VideoRepository, scan_media_records


def _guess_subtitle_path(subtitle_dir: str, basename: str) -> str:
    for ext in (".srt", ".lrc", ".ass"):
        path = os.path.join(subtitle_dir, basename + ext)
        if os.path.exists(path):
            return path
    return ""


def bootstrap_media_database(
    db_path: str,
    mask_dir: str,
    video_dir: str,
    audio_dir: str,
    subtitle_dir: str,
) -> LocalMediaDatabase:
    db = LocalMediaDatabase(db_path)
    db.initialize()

    mask_repo = MaskRepository(db)
    video_repo = VideoRepository(db)
    audio_repo = AudioRepository(db)

    mask_repo.upsert_many([
        MaskRecord(id=None, name=name, mask_path=path, ext=ext)
        for name, path, ext in scan_media_records(mask_dir, (".mp4", ".mov", ".mkv"))
    ])

    video_repo.upsert_many([
        VideoRecord(id=None, name=name, video_path=path, ext=ext)
        for name, path, ext in scan_media_records(video_dir, (".mp4", ".mov", ".mkv"))
    ])

    audio_repo.upsert_many([
        AudioRecord(
            id=None,
            name=name,
            audio_path=path,
            subtitle_path=_guess_subtitle_path(subtitle_dir, name),
            ext=ext,
        )
        for name, path, ext in scan_media_records(audio_dir, (".mp3", ".wav", ".m4a", ".flac"))
    ])

    return db
