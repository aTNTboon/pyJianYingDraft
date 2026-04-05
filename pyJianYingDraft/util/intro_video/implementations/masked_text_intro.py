import os
import random
import uuid
from dataclasses import dataclass

import pyJianYingDraft as draft
from pyJianYingDraft.script_file import ScriptFile
from pyJianYingDraft.time_util import trange
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

    def build(self, start_time: float, track: str, texts: list[str], interval: float = 2.8) -> float:
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

        text_video_material = draft.VideoMaterial(text_video)
        text_video_duration = text_video_material.duration / 1_000_000
        self.script.add_segment(
            draft.VideoSegment(text_video, trange(f"{start_time}s", f"{text_video_duration}s"), volume=0.0),
            track,
        )
        start_time += text_video_duration

        mask_file = os.path.join(self.assets.mask_dir, random.choice(os.listdir(self.assets.mask_dir)))
        output_path = os.path.join(self.assets.output_dir, f"{uuid.uuid4().hex}.mov")
        text_mask = apply_video_mask(
            self.assets.bg_video_path,
            mask_file,
            output_path,
            mode="alpha_from_luma",
        )

        text_mask_material = draft.VideoMaterial(text_mask)
        text_mask_duration = text_mask_material.duration / 1_000_000
        self.script.add_segment(
            draft.VideoSegment(text_mask, trange(f"{start_time}s", f"{text_mask_duration}s"), volume=0.0),
            track,
        )
        return start_time + text_mask_duration
