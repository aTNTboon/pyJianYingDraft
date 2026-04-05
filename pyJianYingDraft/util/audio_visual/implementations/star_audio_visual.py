import math

from PIL import Image, ImageDraw, ImageFilter

from pyJianYingDraft.util.audio_visual.interface import AudioVisual


class StarAudioVisual(AudioVisual):
    def __init__(self, fps: int = 10):
        super().__init__(fps)

    def draw_frame(self, v, t, size=(1920, 1080)) -> Image.Image:
        if isinstance(size, int):
            width = height = size
        else:
            width, height = size

        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        g = ImageDraw.Draw(glow)

        bar_count = 96
        bottom_margin = 70
        bar_area_height = 220
        left_right_margin = 140
        gap = 8

        usable_width = width - left_right_margin * 2
        bar_w = max(4, int((usable_width - gap * (bar_count - 1)) / bar_count))
        total_bars_width = bar_count * bar_w + (bar_count - 1) * gap
        start_x = (width - total_bars_width) // 2
        base_y = height - bottom_margin

        for i in range(bar_count):
            x = start_x + i * (bar_w + gap)
            dist_to_center = abs(i - (bar_count - 1) / 2) / ((bar_count - 1) / 2)
            shape_gain = 1.0 - min(1.0, dist_to_center ** 1.6)
            wave1 = 0.5 + 0.5 * math.sin(t * 1.2 + i * 0.12)
            wave2 = 0.5 + 0.5 * math.sin(t * 0.8 + i * 0.18 + 1.2)
            local = 0.6 * wave1 + 0.4 * wave2
            slow_breath = 0.92 + 0.08 * math.sin(t * 0.9)

            h = 8 + bar_area_height * v * slow_breath * (0.22 + 0.78 * shape_gain) * (0.45 + 0.55 * local)
            top_y = base_y - h
            alpha = int(110 + 120 * v)
            g.rounded_rectangle((x, top_y, x + bar_w, base_y), radius=bar_w // 2, fill=(255, 255, 255, alpha // 2))
            d.rounded_rectangle((x, top_y, x + bar_w, base_y), radius=bar_w // 2, fill=(255, 255, 255, alpha))

        g.rounded_rectangle((left_right_margin, base_y + 8, width - left_right_margin, base_y + 11), radius=2, fill=(255, 255, 255, int(35 + 35 * v)))
        glow = glow.filter(ImageFilter.GaussianBlur(radius=12))
        return Image.alpha_composite(glow, img)
