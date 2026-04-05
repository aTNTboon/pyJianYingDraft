import os
import sqlite3

from pyJianYingDraft.local_db import bootstrap_media_database


def touch(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(b"x")


def test_bootstrap_media_database_creates_and_upserts(tmp_path):
    root = tmp_path / "media"
    mask_dir = root / "mask"
    video_dir = root / "video"
    audio_dir = root / "audio"
    subtitle_dir = root / "subtitle"
    db_path = root / "media.db"

    touch(str(mask_dir / "m1.mov"))
    touch(str(video_dir / "v1.mp4"))
    touch(str(audio_dir / "a1.mp3"))
    touch(str(subtitle_dir / "a1.srt"))

    bootstrap_media_database(
        db_path=str(db_path),
        mask_dir=str(mask_dir),
        video_dir=str(video_dir),
        audio_dir=str(audio_dir),
        subtitle_dir=str(subtitle_dir),
    )

    conn = sqlite3.connect(str(db_path))
    try:
        assert conn.execute("select count(*) from mask").fetchone()[0] == 1
        assert conn.execute("select count(*) from video").fetchone()[0] == 1
        assert conn.execute("select count(*) from audio").fetchone()[0] == 1
        row = conn.execute("select name, subtitle_path from audio").fetchone()
        assert row[0] == "a1"
        assert row[1].endswith("a1.srt")
    finally:
        conn.close()
