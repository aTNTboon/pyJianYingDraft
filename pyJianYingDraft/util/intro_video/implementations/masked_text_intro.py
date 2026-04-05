import os
import random
import uuid
from dataclasses import dataclass

import pyJianYingDraft as draft
from pyJianYingDraft.script_file import ScriptFile
from pyJianYingDraft.time_util import SEC, Timerange
from pyJianYingDraft.track import TrackType
from pyJianYingDraft.util.InterVideo.StartInterVideo import run_text_video_pipeline
from pyJianYingDraft.util.intro_video.interface import IntroVideoInterface
from pyJianYingDraft.util.mask_util import apply_video_mask


@dataclass
class IntroVideoAssets:
    bg_video_path: str
    mask_dir: str
    output_dir: str
    font_path: str = r"C:\Windows\Fonts\simsun.ttc"


class MaskedTextIntroVideo(IntroVideoInterface):
    def __init__(self, script: ScriptFile, assets: IntroVideoAssets):
        self.script = script
        self.assets = assets

    def make_intro_video(self, duration: int, start_time: float, track: str) -> None:
        raise NotImplementedError("该接口保留给兼容实现，推荐使用 build")

    def _to_us(self, seconds_or_us: float | int) -> int:
        # 兼容旧调用(秒)与新调用(微秒): int 且 >= 1秒时按微秒处理
        if isinstance(seconds_or_us, int) and seconds_or_us >= SEC:
            return seconds_or_us
        return int(round(float(seconds_or_us) * SEC))

    def build(self, start_time: float | int, track: str, texts: list[str], interval: float = 2.8) -> int:
        self.script.add_track(TrackType.video, track, relative_index=9999)
        text_video = run_text_video_pipeline(
            texts=texts,
            interval=interval,
            bg_video_path=self.assets.bg_video_path,
            output_path="sad_text_intro.mp4",
            font_path=self.assets.font_path,
            font_size=128,
            fps=30,
            keep_bg_audio=False,
        )

        start_time_us = self._to_us(start_time)
        text_video_material = draft.VideoMaterial(text_video)
        text_video_duration_us = int(text_video_material.duration)
        self.script.add_segment(
            draft.VideoSegment(text_video, Timerange(start_time_us, text_video_duration_us), volume=0.0),
            track,
        )
        start_time_us += text_video_duration_us

        mask_file = os.path.join(self.assets.mask_dir, random.choice(os.listdir(self.assets.mask_dir)))
        output_path = os.path.join(self.assets.output_dir, f"{uuid.uuid4().hex}.mov")
        text_mask = apply_video_mask(
            self.assets.bg_video_path,
            mask_file,
            output_path,
            mode="alpha_from_luma",
        )

        text_mask_material = draft.VideoMaterial(text_mask)
        text_mask_duration_us = int(text_mask_material.duration)
        self.script.add_segment(
            draft.VideoSegment(text_mask, Timerange(start_time_us, text_mask_duration_us), volume=0.0),
            track,
        )
        return start_time_us + text_mask_duration_us
