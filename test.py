import math
import os
import random
import uuid
from dataclasses import dataclass
from pathlib import Path

import pyJianYingDraft as draft
from pymediainfo import MediaInfo

from pyJianYingDraft import SEC, ScriptFile, tim, trange
from pyJianYingDraft.local_db import bootstrap_media_database
from pyJianYingDraft.local_materials import CropSettings, VideoMaterial
from pyJianYingDraft.metadata.mix_mode_meta import MixModeType
from pyJianYingDraft.text_segment import TextSegment
from pyJianYingDraft.track import TrackType
from pyJianYingDraft.util.audio_visual.implementations.ring_audio_visual import RingAudioVisual
from pyJianYingDraft.util.intro_video.implementations.masked_text_intro import IntroVideoAssets, MaskedTextIntroVideo
from pyJianYingDraft.util.lrt2srt import lrc_to_srt
from pyJianYingDraft.util.mask_util import apply_video_mask


@dataclass
class MaterialPaths:
    root_dir: str
    draft_root: str

    @property
    def audio_dir(self) -> str:
        return os.path.join(self.root_dir, "audio")

    @property
    def video_dir(self) -> str:
        return os.path.join(self.root_dir, "video")

    @property
    def mask_dir(self) -> str:
        return os.path.join(self.root_dir, "mask")

    @property
    def subtitle_dir(self) -> str:
        return os.path.join(self.root_dir, "subtitle")

    @property
    def srt_output_dir(self) -> str:
        return os.path.join(self.root_dir, "srt")

    @property
    def intro_temp_dir(self) -> str:
        return os.path.join(self.root_dir, "profix")

    @property
    def db_path(self) -> str:
        return os.path.join(self.root_dir, "media_index.db")


@dataclass
class MusicItem:
    name: str
    path: str


def short_name(name: str, max_len: int = 9) -> str:
    base_name, _ = os.path.splitext(name)
    if len(base_name) <= max_len:
        return f"《{base_name}》"
    return f"《{base_name[:max_len - 3]}...》"


def get_media_duration(path: str, track_type: str) -> float:
    media_info = MediaInfo.parse(path)
    target_track = next((t for t in media_info.tracks if t.track_type == track_type), None)
    if not target_track or not target_track.duration:
        raise ValueError(f"无法读取媒体时长: {path}")
    return target_track.duration / 1000.0


def add_loop_video_to_track(
    script: ScriptFile,
    video_path: str,
    track_name: str,
    start_time: float,
    duration: float,
    intro_type: None | draft.IntroType = None,
    change_type: None | draft.TransitionType = None,
):
    video_duration = get_media_duration(video_path, "Video")
    current = start_time
    end_time = start_time + duration
    video_material = draft.VideoMaterial(video_path, crop_settings=CropSettings())

    first = True
    while current < end_time:
        segment_duration = min(video_duration, end_time - current)
        video_segment = draft.VideoSegment(video_material, trange(f"{current}s", f"{segment_duration}s"), volume=0.0)
        if first and intro_type:
            video_segment.add_animation(intro_type, duration="2s")
        if first and change_type:
            video_segment.add_transition(change_type, duration="1s")
        first = False
        script.add_segment(video_segment, track_name)
        current += segment_duration
    return end_time


def add_subtitle(script: ScriptFile, paths: MaterialPaths, subtitle_file: str, current_start: int, text_track_name: str):
    script.add_track(TrackType.text, text_track_name, relative_index=250)
    suffix = Path(subtitle_file).suffix.lower()
    subtitle_path = subtitle_file

    if suffix == ".lrc":
        os.makedirs(paths.srt_output_dir, exist_ok=True)
        subtitle_path = os.path.join(paths.srt_output_dir, f"{text_track_name}.srt")
        lrc_to_srt(subtitle_file, subtitle_path)
    elif suffix != ".srt":
        raise ValueError(f"不支持的字幕格式: {suffix}")

    style_reference = draft.TextSegment(
        short_name(os.path.basename(subtitle_file)),
        trange(f"{current_start}s", f"{current_start + 10}s"),
        font=draft.FontType.装甲明朝,
        background=draft.TextBackground(color="#000000", alpha=0.25, style=2, round_radius=5),
        style=draft.TextStyle(size=10.0, color=(1, 1, 1), auto_wrapping=True, alpha=0.8, align=1),
        shadow=draft.TextShadow(color=(62 / 255, 210 / 255, 255 / 255), alpha=0.5),
    )
    style_reference.add_animation(draft.TextIntro.轻微放大, duration=tim("0.1s"))
    style_reference.add_animation(draft.TextOutro.缩小, duration=tim("0.15s"))

    script.import_srt(
        subtitle_path,
        track_name=text_track_name,
        style_reference=style_reference,
        clip_settings=draft.ClipSettings(transform_y=-0.4),
        time_offset=f"{current_start}s",
    )


def add_video_grid(script: ScriptFile, video_items: list[MusicItem], start_time: float, duration: float, track_prefix: str, width: int, height: int, source_video_dir: str):
    if not video_items:
        return

    random_tag = str(uuid.uuid4())
    row = math.ceil(math.sqrt(len(video_items)))
    col = math.ceil(len(video_items) / row)
    cell_width = width / col
    cell_height = height / row

    selected = set()
    for i, item in enumerate(video_items):
        r = i // col
        c = i % col

        selected_video = os.path.join(source_video_dir, random.choice(os.listdir(source_video_dir)))
        while selected_video in selected:
            selected_video = os.path.join(source_video_dir, random.choice(os.listdir(source_video_dir)))
        selected.add(selected_video)

        video_material = draft.VideoMaterial(selected_video)
        if not video_material.width or not video_material.height:
            continue

        scale = max(cell_width / video_material.width, cell_height / video_material.height)
        center_x_px = c * cell_width + cell_width / 2
        center_y_px = r * cell_height + cell_height / 2
        transform_x = (center_x_px - width / 2) / (width / 2)
        transform_y = (center_y_px - height / 2) / (height / 2)

        clip_settings = draft.ClipSettings(scale_x=scale, scale_y=scale, transform_x=transform_x, transform_y=transform_y)
        video_segment = draft.VideoSegment(video_material, trange(f"{start_time}s", f"{duration}s"), clip_settings=clip_settings, volume=0.0)
        video_segment.add_animation(draft.IntroType.渐显, duration=tim("1s"))
        video_segment.add_animation(draft.OutroType.渐隐, duration=tim("1s"))

        track_name = f"{track_prefix}{random_tag}_{i}"
        script.add_track(draft.TrackType.video, track_name, relative_index=i)
        script.add_segment(video_segment, track_name)

        text_segment = TextSegment(
            short_name(item.name),
            video_segment.target_timerange,
            font=draft.FontType.装甲明朝,
            style=draft.TextStyle(color=(1.0, 1.0, 1.0)),
            clip_settings=draft.ClipSettings(scale_x=0.8, scale_y=0.8, transform_x=transform_x, transform_y=transform_y),
            shadow=draft.TextShadow(color=(38 / 255, 139 / 255, 193 / 255), alpha=0.2),
        )
        text_segment.add_animation(draft.TextIntro.渐显, duration=tim("1s"))
        text_segment.add_animation(draft.TextOutro.渐隐, duration=tim("0.5s"))
        text_track_name = f"{track_prefix}{random_tag}_text_{i}"
        script.add_track(draft.TrackType.text, text_track_name, relative_index=0)
        script.add_segment(text_segment, text_track_name)


def main_audio_with_video(script: ScriptFile, paths: MaterialPaths, audios: list[str], subtitles: list[str], current_start: int, sum_video: list[MusicItem]):
    audio_track_name = "主音乐轨"
    video_track_name = "主视频轨"
    visual_track_name = "主视频音频可视化轨"
    linked_track_name = "主视频链接轨"
    subtitle_track_prefix = "字幕轨"

    for track_type, track_name, index in [
        (draft.TrackType.audio, audio_track_name, None),
        (draft.TrackType.video, video_track_name, None),
        (draft.TrackType.video, visual_track_name, 501),
        (draft.TrackType.video, linked_track_name, 200),
    ]:
        if index is None:
            script.add_track(track_type, track_name)
        else:
            script.add_track(track_type, track_name, relative_index=index)

    videos = set()
    while len(videos) < len(audios):
        videos.add(random.choice(os.listdir(paths.video_dir)))

    sum_time = current_start
    for i, audio in enumerate(audios):
        audio_file = os.path.join(paths.audio_dir, audio)
        duration_sec = get_media_duration(audio_file, "Audio")

        current_video = videos.pop()
        linked_video_duration = 0

        if videos:
            next_video = list(videos)[-1]
            output_path = apply_video_mask(
                os.path.join(paths.video_dir, current_video),
                os.path.join(paths.mask_dir, random.choice(os.listdir(paths.mask_dir))),
                os.path.join(paths.intro_temp_dir, f"{uuid.uuid4().hex}.mov"),
                mode="alpha_from_luma",
                keep_audio=False,
            )
            linked_material = draft.VideoMaterial(output_path)
            linked_video_duration = linked_material.duration / 1_000_000
            mask_segment = draft.VideoSegment(
                linked_material,
                trange(f"{current_start + duration_sec - linked_video_duration - 0.2}s", f"{linked_video_duration}s"),
                volume=0.0,
            )
            mask_segment.add_animation(draft.OutroType.渐隐)
            script.add_segment(mask_segment, linked_track_name)
            add_loop_video_to_track(
                script,
                os.path.join(paths.video_dir, next_video),
                video_track_name,
                current_start + duration_sec - linked_video_duration,
                linked_video_duration,
                change_type=draft.TransitionType.叠化,
            )

        add_loop_video_to_track(script, os.path.join(paths.video_dir, current_video), video_track_name, current_start, duration_sec - linked_video_duration)

        result_video = RingAudioVisual().make_video(audio_file)
        result_material = draft.VideoMaterial(result_video)
        visual_segment = draft.VideoSegment(
            result_material,
            trange(f"{current_start}s", f"{result_material.duration / 1_000_000}s"),
            clip_settings=draft.ClipSettings(alpha=0.6),
        )
        script.add_segment(visual_segment, visual_track_name)

        add_subtitle(script, paths, subtitles[i], current_start=current_start, text_track_name=f"{subtitle_track_prefix}{i}")
        audio_segment = draft.AudioSegment(audio_file, trange(f"{current_start}s", f"{duration_sec}s"), volume=0.6)
        script.add_segment(audio_segment, audio_track_name)

        current_start += duration_sec
        if videos:
            add_video_grid(script, sum_video, start_time=current_start + 2, duration=4, track_prefix="九宫格", width=1920, height=1080, source_video_dir=paths.video_dir)
        sum_time = duration_sec

    return sum_time


def run_demo(material_root: str = r"D:\video", draft_root: str = r"D:\jianying\JianyingPro Drafts"):
    paths = MaterialPaths(root_dir=material_root, draft_root=draft_root)
    os.makedirs(paths.intro_temp_dir, exist_ok=True)

    bootstrap_media_database(
        db_path=paths.db_path,
        mask_dir=paths.mask_dir,
        video_dir=paths.video_dir,
        audio_dir=paths.audio_dir,
        subtitle_dir=paths.subtitle_dir,
    )

    draft_folder = draft.DraftFolder(paths.draft_root)
    script = draft_folder.create_draft("demo2", 1920, 1080, allow_replace=True)
    script.add_track(draft.TrackType.video, "视频轨", relative_index=0)

    videos = [random.choice(os.listdir(paths.audio_dir)) for _ in range(1, 10)]
    video_list = [MusicItem(name=video, path=os.path.join(paths.audio_dir, video)) for video in videos]

    intro_builder = MaskedTextIntroVideo(
        script,
        IntroVideoAssets(
            bg_video_path=os.path.join(paths.video_dir, "灵梦.mp4"),
            mask_dir=paths.mask_dir,
            output_dir=paths.intro_temp_dir,
        ),
    )

    current_time = intro_builder.build(start_time=0, track="开场视频轨", texts=["你是否愿意再陪我去看一次长岛的雪"]) / SEC
    current_time += 2

    add_video_grid(
        script,
        video_list,
        start_time=current_time,
        duration=4.5,
        track_prefix="视频轨",
        width=1920,
        height=1080,
        source_video_dir=paths.video_dir,
    )

    audios = sorted(os.listdir(paths.audio_dir))
    subtitles = [os.path.join(paths.subtitle_dir, "test.lrc") for _ in audios]
    current_time += main_audio_with_video(script, paths, audios, subtitles, current_start=3, sum_video=video_list)
    script.save()


if __name__ == "__main__":
    run_demo()
