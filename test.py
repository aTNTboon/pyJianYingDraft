from datetime import date
import math
import os
from pathlib import Path
import random
import time
import uuid
from pymediainfo import MediaInfo
from pyJianYingDraft import ScriptFile
import pyJianYingDraft as draft
from pyJianYingDraft import trange
import math
import pyJianYingDraft as draft
from pyJianYingDraft import trange
import math
import os
import random
from pyJianYingDraft.local_materials import CropSettings, VideoMaterial
from pyJianYingDraft.metadata.mix_mode_meta import MixModeType
from pyJianYingDraft.text_segment import TextSegment
from pyJianYingDraft.time_util import Timerange, tim
from pyJianYingDraft.track import TrackType
from pyJianYingDraft.video_segment import MixMode, VideoSegment
from pyJianYingDraft.util.AudioVisual.RetrangleAudioVisual import RingAudioVisual
from pyJianYingDraft.util.lrt2srt import lrc_to_srt
from pyJianYingDraft.util.mask_util import apply_video_mask
material_dir = r"D:\video"
MATERIAL_AUDIO_DIR = os.path.join(material_dir, "audio")
MATERIAL_VIDEO_DIR = os.path.join(material_dir, "video")
MATERIAL_MUSIC_DIR = os.path.join(material_dir, "music")
SUM_VIDEO_TRACK="视频轨"
MASK_DIR="D:\\video\\mask\\"
def add_loop_video_to_track(
        script,
        video_path: str,
        track_name: str,
        start_time: float,
        duration: float,
        intro_type:None|draft.IntroType=None,
        change_type:None|draft.TransitionType=None,

):
    """
    在指定轨道上，将同一个视频循环铺满指定时长。

    参数:
        script: draft script 对象
        video_path: 视频文件路径
        track_name: 轨道名
        start_time: 开始时间，单位秒
        duration: 持续时间，单位秒
    """
    media_info = MediaInfo.parse(video_path)
    video_track = next((t for t in media_info.tracks if t.track_type == "Video"), None)

    if not video_track or not video_track.duration:
        raise ValueError(f"无法读取视频时长: {video_path}")

    video_duration = video_track.duration / 1000.0
    if video_duration <= 0:
        raise ValueError(f"视频时长无效: {video_path}")

    current = start_time
    end_time = start_time + duration
    
    video_material = draft.VideoMaterial(video_path,crop_settings=CropSettings())
    first=True

    while current < end_time:
        remaining = end_time - current
        segment_duration = min(video_duration, remaining)

        video_segment = draft.VideoSegment(
            video_material,
            trange(f"{current}s", f"{segment_duration}s"),
            volume=0.0
        )
        if(first and intro_type):
            video_segment.add_animation(intro_type,duration="2s")
            first=False
        if(first and change_type):
            video_segment.add_transition(change_type,duration="1s")
            first=False

        script.add_segment(video_segment, track_name)
        current += segment_duration
    return end_time



import os

def short_name(name: str, max_len: int = 9) -> str:
    # 去掉文件后缀
    base_name, ext = os.path.splitext(name)
    # 如果去掉后缀的长度 <= max_len，直接返回
    if len(base_name) <= max_len:
        return  "《"+base_name+"》"
    # 否则截断并加省略号
    return "《"+base_name[:max_len - 3] + "..."+"》"
def get_item_name_and_path(item):
    """
    兼容两种传入方式：
    1. dict: {"name": "...", "path": "..."}
    2. object: item.name / item.path
    """
    if isinstance(item, dict):
        return item.get("name", ""), item.get("path", "")
    return getattr(item, "name", ""), getattr(item, "path", "")
class Music_item:
    def __init__(self, name, path):
        self.name = name
        self.path = path

# Windows 路径
from pyJianYingDraft.util.InterVideo.StartInterVideo import run_text_video_pipeline
def intro_make(script:ScriptFile,start_time:int,track:str,bg_video_path:str=r"D:\video\video\灵梦.mp4",texts:list[str]=["测试"]):
        
    script.add_track(TrackType.video,track,relative_index=9999)
    text_video= run_text_video_pipeline(
    texts=texts,
    interval=2.8,
    bg_video_path=bg_video_path,
    output_path="sad_text_intro.mp4",
    font_path=r"C:\Windows\Fonts\simsun.ttc",
    font_size=128,
    fps=30,
    keep_bg_audio=False)
    text_video_material:VideoMaterial=draft.VideoMaterial(text_video)
    text_video_material_time = text_video_material.duration/1000000
    video_segment:VideoSegment = draft.VideoSegment(
            text_video,
            trange(f"{start_time}s", f"{text_video_material_time}s"),
            volume=0.0
        )
    script.add_segment(video_segment, track)
    start_time=start_time+int(text_video_material_time)

    text_mask= apply_video_mask(bg_video_path,os.path.join(MASK_DIR,random.choice(os.listdir(MASK_DIR))),f"D:\\video\\profix\\{uuid.uuid4().hex}.mov",mode="alpha_from_luma")
    text_mask_material:VideoMaterial=draft.VideoMaterial(text_mask)
    text_mask_material_time = text_mask_material.duration/1000000
    video_segment:VideoSegment = draft.VideoSegment(
            text_mask,
            trange(f"{start_time}s", f"{text_mask_material_time}s"),
            volume=0.0,
        )
    script.add_segment(video_segment, track)
    start_time=start_time+int(text_mask_material_time)
    return start_time



def add__video_to_sum_track(
    script:ScriptFile,
    video_items:list[Music_item],   # 改成对象数组
    start_time: float,
    duration: float,
    track_prefix: str,
    width: int,
    height: int
):

    strnew=str(uuid.uuid4())
    n = len(video_items)
    if n == 0:
        return
    choiced_videos = set()
    row = math.ceil(math.sqrt(n))
    col = math.ceil(n / row)

    cell_width = width / col
    cell_height = height / row

    for i, item in enumerate(video_items):
        name, path = get_item_name_and_path(item)
        if not path:
            continue

        r = i // col
        c = i % col
        choiced_video=os.path.join(MATERIAL_VIDEO_DIR, random.choice(os.listdir(MATERIAL_VIDEO_DIR)))
        while choiced_video in choiced_videos:
            choiced_video=os.path.join(MATERIAL_VIDEO_DIR, random.choice(os.listdir(MATERIAL_VIDEO_DIR)))
        choiced_videos.add(choiced_video)
        video_material = draft.VideoMaterial(choiced_video)
        material_width, material_height = video_material.width, video_material.height
        if not material_width or not material_height:
            continue

        # 文字改成传入对象里的 name
        name = short_name(str(name))

        # 等比铺满格子，不变形，可能裁边
        scale = max(cell_width / material_width, cell_height / material_height)

        # 当前格子中心点（像素）
        center_x_px = c * cell_width + cell_width / 2
        center_y_px = r * cell_height + cell_height / 2

        # 转为 transform 坐标
        transform_x = (center_x_px - width / 2) / (width / 2)
        transform_y = (center_y_px - height / 2) / (height / 2)

        clip_settings = draft.ClipSettings()
        clip_settings.alpha = 1.0
        clip_settings.flip_horizontal = False
        clip_settings.flip_vertical = False
        clip_settings.rotation = 0.0
        clip_settings.scale_x = scale
        clip_settings.scale_y = scale
        clip_settings.transform_x = transform_x
        clip_settings.transform_y = transform_y
        video_segment = draft.VideoSegment(
            video_material,
            trange(f"{start_time}s", f"{duration}s"),
            clip_settings=clip_settings,
            volume=0.0
        )
        video_segment.add_animation(draft.IntroType.渐显, duration=tim(f"1s"))
        video_segment.add_animation(draft.OutroType.渐隐, duration=tim(f"1s"))
        track_name = f"{track_prefix}{strnew}_{i}"
        script.add_track(draft.TrackType.video, track_name,relative_index=i)
        script.add_segment(video_segment, track_name)

        print(f"第{i}个小块显示名字: {name}")

        text_segment = draft.TextSegment(
            name,
            video_segment.target_timerange,
            font=draft.FontType.装甲明朝,
            style=draft.TextStyle(color=(1.0, 1.0, 1.0)),
            clip_settings=draft.ClipSettings(
                scale_x=0.8,
                scale_y=0.8,
                transform_x=transform_x,
                transform_y=transform_y
            ),
            shadow=draft.TextShadow(color=(38/255, 139/255, 193/255), alpha=0.2)
        )
        text_segment.add_animation(draft.TextIntro.渐显, duration=tim(f"1s"))
        text_segment.add_animation(draft.TextOutro.渐隐, duration=tim(f"0.5s"))
        track_text_name = f"{track_prefix}{strnew}_text_{i}"
        script.add_track(draft.TrackType.text, track_text_name,relative_index =0)
        script.add_segment(text_segment,track_text_name)



def set_main_begin(image_path: str, duration: float):
    
    image_material = draft.VideoMaterial(image_path)
    video_segment = draft.VideoSegment(image_material,
                                    trange("0s",f"{duration}s"), clip_settings=draft.ClipSettings(alpha=0.17),volume=0.0,)  # 紧跟上一片段，长度与gif一致
    video_segment.add_background_filling("blur", 0.0625)  # 添加一个模糊背景填充效果, 模糊程度等同于剪映中第一档
    video_segment.set_mix_mode(MixModeType.强光)  # 设置混合模式为正常，确保背景填充效果可见
    return video_segment



def set_front_scene():
    video_segment=set_main_begin(image_path="D:\\video\\image\\test.png", duration=3)

    video_segment.add_effect(draft.VideoSceneEffectType.星火)
    MAIN_BEGIN_TRACK_NAME = "主前景轨"
    script.add_track(draft.TrackType.video, MAIN_BEGIN_TRACK_NAME,relative_index=100)
    script.add_segment(video_segment, MAIN_BEGIN_TRACK_NAME)

# def set_mengban_main(top:str,center:str,bottom:str,start:int,duration:int):
#     MENGBAN_TRACK_TOP_NAME= "蒙版轨-上-被裁剪"
#     MENGBAN_TRACK_CENTER_NAME= "蒙版轨-中-黑白素材"
#     MENGBAN_TRACK_BOTTOM_NAME= "蒙版轨-下-白色范围"

#     script.add_track(draft.TrackType.video, MENGBAN_TRACK_TOP_NAME,relative_index=2)
#     script.add_track(draft.TrackType.video, MENGBAN_TRACK_CENTER_NAME,relative_index=1)
#     script.add_track(draft.TrackType.video, MENGBAN_TRACK_BOTTOM_NAME,relative_index=0)
#     top_image=draft.VideoMaterial(top)
#     center_image=draft.VideoMaterial(center)
#     bottom_image=draft.VideoMaterial(bottom)
#     top_segment=draft.VideoSegment(top_image,trange(f"{start}s",f"{ duration}s"),clip_settings=draft.ClipSettings(alpha=0.5),volume=0.0)

#     center_segment=draft.VideoSegment(center_image,trange(f"{start}s",f"{ duration}s"),clip_settings=draft.ClipSettings(alpha=0.5),volume=0.0)
#     center_segment.set_mix_mode(MixModeType.滤色)
#     bottom_segment=draft.VideoSegment(bottom_image,trange(f"{start}s",f"{ duration}s"),clip_settings=draft.ClipSettings(alpha=0.5),volume=0.0)



def add_subtitle(script: ScriptFile, srt_path: str, current_start: int, text_track_name: str):

    script.add_track(draft.TrackType.text,text_track_name , relative_index=250)
    path = Path(srt_path)
    suffix = path.suffix.lower()
    subtitle_path=srt_path
    if suffix == ".lrc":
        new_srt_path=f"D:\\video\\srt\\{text_track_name}.srt"
        subtitle_path=new_srt_path
        lrc_to_srt(srt_path, new_srt_path.replace(".lrc", ".srt"))
    elif suffix == ".srt":
        subtitle_path = srt_path
    else:
        raise ValueError(f"不支持的字幕格式: {suffix}")

    text_style:TextSegment= draft.TextSegment(
        short_name(os.path.basename(srt_path)),
        trange(f"{current_start}s", f"{current_start + 10}s"),
        font=draft.FontType.装甲明朝,
        background=draft.TextBackground(color="#000000", alpha=0.25,style=2,round_radius=5),
        style=draft.TextStyle(size=10.0, color=(1,1, 1),auto_wrapping =True,alpha=0.8,align=1),
        shadow=draft.TextShadow(color=(62/255, 210/255,255/255), alpha=0.5),
    )
    text_style.add_animation(draft.TextIntro.轻微放大, duration=tim(f"0.1s"))
    text_style.add_animation(draft.TextOutro.缩小, duration=tim(f"0.15s"))
    script.import_srt(subtitle_path, track_name=text_track_name,
                style_reference=text_style,
                clip_settings=draft.ClipSettings(transform_y=-0.4),time_offset=f"{current_start}s")  # 将字幕放置在屏幕上方



def main_audio_with_video(script:ScriptFile,audios:list[str],srtList:list[str],current_start:int,sum_video:list[Music_item]):
    audio_track_name = "主音乐轨"
    video_track_name = "主视频轨"
    video_audio_visual_track_name = "主视频音频可视化轨"
    name_track_name = "主视频名字轨"
    linked_video_material_track_name="主视频链接轨"
    srt_track_name = "字幕轨"
    sum_track_list:list[str] = [f"{SUM_VIDEO_TRACK}_{i}" for i in range(len(audios))]

    script.add_track(draft.TrackType.audio, audio_track_name)
    script.add_track(draft.TrackType.video, video_track_name)
    script.add_track(draft.TrackType.video, video_audio_visual_track_name, relative_index=501)
    script.add_track(draft.TrackType.video, linked_video_material_track_name, relative_index=200)
    script.add_track(draft.TrackType.text, name_track_name, relative_index=125)
    first=True

    videos:set[str] = set()
    while len(videos)<len(audios):
        videos.add(random.choice(os.listdir(MATERIAL_VIDEO_DIR)))

    assert audios
    sum_time=current_start
    for i, audio in enumerate(audios):
        audio_file = os.path.join(MATERIAL_AUDIO_DIR, audio)

        media_info = MediaInfo.parse(audio_file)
        audio_track = next((t for t in media_info.tracks if t.track_type == "Audio"), None)
        if not audio_track or not audio_track.duration:
            continue
        duration_sec = audio_track.duration / 1000.0
        #todo
        #todo
        #todo
        #todo视频怎么传后期改
        current_video_path=videos.pop()
        linked_video_material_time=0

        ##中间蒙版部分
        if(len(videos)!=0):
            video_list=list(videos)
            next_video_path=video_list[-1]

            output_path=apply_video_mask(os.path.join(MATERIAL_VIDEO_DIR, current_video_path),os.path.join(MASK_DIR,random.choice(os.listdir(MASK_DIR))),f"D:\\video\\profix\\{uuid.uuid4().hex}.mov",mode="alpha_from_luma",keep_audio=False)

            
            linked_video_material=draft.VideoMaterial(output_path)
            linked_video_material_time = linked_video_material.duration/1000000
            video_segment=draft.VideoSegment(linked_video_material,trange(f"{current_start+ duration_sec- linked_video_material_time-0.2}s",f"{linked_video_material_time}s"),volume=0.0)
            video_segment.add_animation(draft.OutroType.渐隐)
            vi
            script.add_segment(video_segment, linked_video_material_track_name)
            add_loop_video_to_track(
            script,
            os.path.join(MATERIAL_VIDEO_DIR, next_video_path),
            video_track_name,
            current_start+duration_sec- linked_video_material_time,
            linked_video_material_time,
            change_type=draft.TransitionType.叠化
        )
        add_loop_video_to_track(
            script,
            os.path.join(MATERIAL_VIDEO_DIR, current_video_path),
            video_track_name,
            current_start,
            duration_sec- linked_video_material_time,
        )
        
        ## 视频可视化部分，声音也在这里
        result: str = RingAudioVisual().make_video(audio_file)
        result_video_material = draft.VideoMaterial(result)
        video_visual_segment = draft.VideoSegment(
            result_video_material,
            trange(f"{current_start}s", f"{result_video_material.duration/1000000}s"),
            clip_settings=draft.ClipSettings(alpha=0.6)
        )
        script.add_segment(video_visual_segment, video_audio_visual_track_name)
        
        ##增加字幕
        add_subtitle(script, srt_path=srtList[i], current_start=current_start, text_track_name=f"{srt_track_name}{i}")
        audio_segment = draft.AudioSegment(
            audio_file,
            trange(f"{current_start}s", f"{duration_sec}s"),
            volume=0.6,
        )

        audio_name=draft.TextSegment(
            short_name(audio),
            audio_segment.target_timerange,
            font=draft.FontType.飞扬行书,
            style=draft.TextStyle(color=(1.0, 1.0, 1.0),size=9,align=1),
            clip_settings=draft.ClipSettings(
                scale_x=1,
                scale_y=1,
                transform_x=-0.8,
                transform_y=0.7,
            ),
            shadow=draft.TextShadow(color=(38/255, 139/255, 193/255), alpha=0.2)
        )
        script.add_segment(audio_name, name_track_name)
        script.add_segment(audio_segment, audio_track_name)
        current_start += duration_sec
        if(len(videos)!=0):
            add__video_to_sum_track(
                    script,
                    sum_video,
                    start_time=current_start+2,
                    duration=4,
                    track_prefix="test",
                    width=1920,
                    height=1080,
                )
        sum_time=duration_sec
    return sum_time



draft_folder = draft.DraftFolder(r"D:\jianying\JianyingPro Drafts")
script = draft_folder.create_draft("demo2", 1920, 1080, allow_replace=True)

script.add_track(draft.TrackType.video, SUM_VIDEO_TRACK,relative_index=0)
videos=[ random.choice(os.listdir(MATERIAL_AUDIO_DIR)) for i in range(1,10) ]


current_time=0
open_video_track_name="开场视频轨"

current_time= intro_make(script,current_time,"开场视频轨",texts=["你是否愿意再陪我去看一次长岛的雪"])
current_time+=2
video_list=[Music_item(name=video, path=os.path.join(MATERIAL_AUDIO_DIR, video)) for video in videos]
nine_square_grid_time=4.5
add__video_to_sum_track(
    script,
    video_list,
    start_time=current_time,
    duration=nine_square_grid_time,
    track_prefix=SUM_VIDEO_TRACK,
    width=1920,
    height=1080,
)
# video=random.choice(os.listdir(MATERIAL_AUDIO_DIR)) 
# path=os.path.join(MATERIAL_AUDIO_DIR, video)
# def set_background(video_path: str,duration:float):
#     BACKGROUND_TRACK_NAME = "背景轨"
#     script.add_track(draft.TrackType.video, BACKGROUND_TRACK_NAME)
#     add_loop_video_to_track(script, video_path, BACKGROUND_TRACK_NAME, 0, duration)  # 持续时间设置得足够长，确保覆盖整个视频长度
# BACKGROUND_FILE:str=""
# BACKGOUND_TRACK_NAME = "背景轨"
# script.add_track(draft.TrackType.audio, BACKGOUND_TRACK_NAME)
# add_loop_video_to_track(script, MATERIAL_VIDEO_DIR, BACKGOUND_TRACK_NAME, 0, sum_time)

audios = sorted(os.listdir(MATERIAL_AUDIO_DIR))

current_time+= main_audio_with_video(script,audios,srtList=["D:\\video\\subtitle\\test.lrc","D:\\video\\subtitle\\test.lrc"],current_start=3,sum_video=video_list)
script.save()