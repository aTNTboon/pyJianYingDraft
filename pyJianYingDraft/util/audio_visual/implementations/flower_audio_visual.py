import math

from PIL import Image, ImageDraw, ImageFilter

from pyJianYingDraft.util.audio_visual.interface import AudioVisual


class FlowerAudioVisual(AudioVisual):
    def __init__(self, fps: int = 30):
        super().__init__(fps)

    def draw_frame(self, v, t, size=512) -> Image.Image:
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        glow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        g = ImageDraw.Draw(glow)

        cx = cy = size // 2
        bar_count = 64
        max_h = size * 0.28
        width = max(3, size // 120)
        radius = size * 0.22

        for i in range(bar_count):
            ang = i / bar_count * math.tau + t * 0.15
            local = 0.35 + 0.65 * (0.5 + 0.5 * math.sin(i * 0.45 + t * 2.4))
            h = 12 + max_h * v * local

            x1 = cx + math.cos(ang) * radius
            y1 = cy + math.sin(ang) * radius
            x2 = cx + math.cos(ang) * (radius + h)
            y2 = cy + math.sin(ang) * (radius + h)

            alpha = int(90 + 150 * v)
            g.line((x1, y1, x2, y2), fill=(255, 255, 255, alpha // 2), width=width + 4)
            d.line((x1, y1, x2, y2), fill=(255, 255, 255, alpha), width=width)

        core = size * (0.08 + 0.08 * v)
        d.ellipse((cx - core, cy - core, cx + core, cy + core), fill=(255, 255, 255, int(180 + 60 * v)))
        glow = glow.filter(ImageFilter.GaussianBlur(radius=10))
        return Image.alpha_composite(glow, img)
