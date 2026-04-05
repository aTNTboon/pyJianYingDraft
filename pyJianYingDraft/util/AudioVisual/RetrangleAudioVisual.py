import numpy as np
from moviepy import AudioFileClip
from PIL import Image, ImageDraw
import subprocess, os
from pyJianYingDraft.util.AudioVisualInterface import AudioVisual
import math
from PIL import Image, ImageDraw, ImageFilter

class RingAudioVisual(AudioVisual):
    def __init__(self, fps=10):
        super().__init__(fps)

    def draw_frame(self, v, t, size=(1920, 1080)) -> Image.Image:
        width, height = size

        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))

        d = ImageDraw.Draw(img)
        g = ImageDraw.Draw(glow)

        # 频谱放在底部
        bar_count = 96
        bottom_margin = 10
        bar_area_height = 300
        left_right_margin = 140
        gap = 8

        usable_width = width - left_right_margin * 2
        bar_w = max(4, int((usable_width - gap * (bar_count - 1)) / bar_count))
        total_bars_width = bar_count * bar_w + (bar_count - 1) * gap
        start_x = (width - total_bars_width) // 2
        base_y = height - bottom_margin

        # 中间高、两边低的整体轮廓
        center_boost_width = bar_count * 0.32

        for i in range(bar_count):
            x = start_x + i * (bar_w + gap)

            dist_to_center = abs(i - (bar_count - 1) / 2) / ((bar_count - 1) / 2)
            shape_gain = 1.0 - min(1.0, dist_to_center ** 1.6)

            # 让每根柱子有自己的动态
            wave1 = 0.5 + 0.5 * math.sin(t * 6.0 + i * 0.22)
            wave2 = 0.5 + 0.5 * math.sin(t * 3.8 + i * 0.37 + 1.2)
            local = 0.55 * wave1 + 0.45 * wave2

            # 最终高度
            h = 8 + bar_area_height * v * (0.18 + 0.82 * shape_gain) * (0.35 + 0.65 * local)

            top_y = base_y - h

            alpha = int(110 + 120 * v)

            # 发光层
            g.rounded_rectangle(
                (x, top_y, x + bar_w, base_y),
                radius=bar_w // 2,
                fill=(255, 255, 255, alpha // 2)
            )

            # 主体层
            d.rounded_rectangle(
                (x, top_y, x + bar_w, base_y),
                radius=bar_w // 2,
                fill=(255, 255, 255, alpha)
            )

        # 底部一条柔光基线
        line_y = base_y + 8
        g.rounded_rectangle(
            (left_right_margin, line_y, width - left_right_margin, line_y + 3),
            radius=2,
            fill=(255, 255, 255, int(40 + 40 * v))
        )

        glow = glow.filter(ImageFilter.GaussianBlur(radius=12))
        img = Image.alpha_composite(glow, img)
        return img