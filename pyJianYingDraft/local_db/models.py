from dataclasses import dataclass


@dataclass
class MaskRecord:
    id: int | None
    name: str
    mask_path: str
    ext: str


@dataclass
class VideoRecord:
    id: int | None
    name: str
    video_path: str
    ext: str


@dataclass
class AudioRecord:
    id: int | None
    name: str
    audio_path: str
    subtitle_path: str
    ext: str
    tags: str = ""
    duration_seconds: float = 0.0
