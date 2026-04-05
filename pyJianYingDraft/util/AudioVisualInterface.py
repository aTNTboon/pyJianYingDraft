import shutil
import uuid

import numpy as np
from moviepy import AudioFileClip
from PIL import Image, ImageDraw
import subprocess, os
from abc import ABC, abstractmethod


class AudioVisual(ABC):
    def __init__(self, fps=10):
        self.fps = fps
        self.tempfile_dir = os.path.join(os.path.dirname(__file__), "tempfiles")
    @abstractmethod
    def draw_frame(self, v, t, size)->Image.Image:
        pass
    def load_audio_values(self,audio_path):
        audio = AudioFileClip(audio_path)
        samples = audio.to_soundarray(fps=44100)
        audio.close()

        mono = samples.mean(axis=1)
        chunk = 44100 // self.fps

        values = []
        for i in range(0, len(mono), chunk):
            part = mono[i:i+chunk]
            if len(part) == 0:
                break
            v = np.sqrt(np.mean(part**2))
            values.append(v)

        values = np.array(values)
        values /= values.max() + 1e-6
        return values



    def make_video(self, audio_path):
        values = self.load_audio_values(audio_path)
        width, height = 1920, 1080
        values = self.load_audio_values(audio_path) 
        task_id = str(uuid.uuid4()) 
        temp_root = self.tempfile_dir 
        if not os.path.exists(temp_root): 
            os.mkdir(temp_root) 
        work_dir = os.path.join(temp_root, task_id) 
        frames_dir = os.path.join(work_dir, "frames") 
        output_path = os.path.join(work_dir, "out.mov") 
        if os.path.exists(frames_dir): 
            shutil.rmtree(frames_dir) 
        os.makedirs(frames_dir, exist_ok=True)

        # ffmpeg 命令：从 pipe 输入 raw RGBA，输出 MOV
        cmd = [
            "ffmpeg",
            "-y",
            "-f", "rawvideo",
            "-pix_fmt", "rgba",
            "-s", f"{width}x{height}",
            "-r", str(self.fps),
            "-i", "pipe:0",
            "-i", audio_path,
            "-c:v", "prores_ks",
            "-pix_fmt", "yuva444p10le",
            "-profile:v", "4",
            "-c:a", "aac",
            "-shortest",
            output_path
        ]

        # 启动 ffmpeg 子进程
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

        for i, v in enumerate(values):
            img: Image.Image = self.draw_frame(v, t=i / self.fps, size=(width, height))
            if img is None:
                raise ValueError("请实现方法 draw_frame，返回一张PIL.Image对象")
            
            # 转成 raw RGBA bytes
            frame_bytes = img.tobytes()
            proc.stdin.write(frame_bytes)

        proc.stdin.close()
        proc.wait()

        return output_path
