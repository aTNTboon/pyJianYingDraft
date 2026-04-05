import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from moviepy import VideoFileClip, VideoClip


# =========================
# Utils
# =========================
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease_in_out(x: float) -> float:
    return 0.5 - 0.5 * math.cos(math.pi * clamp(x))


def break_text(text: str, every: int = 12) -> str:
    text = text.strip()
    if "\n" in text:
        return text
    if len(text) <= every:
        return text
    return "\n".join(text[i:i + every] for i in range(0, len(text), every))


def make_vertical_gradient(size, top_color, bottom_color):
    w, h = size
    arr = np.zeros((h, w, 4), dtype=np.uint8)
    for y in range(h):
        t = y / max(1, h - 1)
        arr[y, :, 0] = int(top_color[0] * (1 - t) + bottom_color[0] * t)
        arr[y, :, 1] = int(top_color[1] * (1 - t) + bottom_color[1] * t)
        arr[y, :, 2] = int(top_color[2] * (1 - t) + bottom_color[2] * t)
        arr[y, :, 3] = int(top_color[3] * (1 - t) + bottom_color[3] * t)
    return Image.fromarray(arr, "RGBA")


def cover_resize_np(frame: np.ndarray, target_w: int, target_h: int) -> Image.Image:
    img = Image.fromarray(frame).convert("RGB")
    src_w, src_h = img.size
    src_ratio = src_w / src_h
    dst_ratio = target_w / target_h

    if src_ratio > dst_ratio:
        new_h = target_h
        new_w = int(new_h * src_ratio)
    else:
        new_w = target_w
        new_h = int(new_w / src_ratio)

    img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    img = img.crop((left, top, left + target_w, top + target_h))
    return img.convert("RGBA")


# =========================
# Font cache
# =========================
_FONT_CACHE = {}


def get_font(font_path: str, font_size: int):
    key = (font_path, font_size)
    if key not in _FONT_CACHE:
        _FONT_CACHE[key] = ImageFont.truetype(font_path, font_size)
    return _FONT_CACHE[key]


# =========================
# Styled text render
# 只 blur 一次
# =========================
def render_styled_text(
    canvas_size,
    text,
    font_path,
    font_size=120,
    progress=0.5,
    base_y_ratio=0.5,
    letter_spacing=6,
    blur_radius=6,
):
    width, height = canvas_size

    fade_in = clamp(progress / 0.18)
    fade_out = clamp((1.0 - progress) / 0.22)
    alpha_factor = ease_in_out(min(fade_in, fade_out))

    drift_y = -10 * ease_in_out(progress)
    scale = 1.015 - 0.015 * ease_in_out(progress)
    current_font_size = max(10, int(font_size * scale))

    font = get_font(font_path, current_font_size)

    text = break_text(text, every=12)
    lines = text.split("\n")

    line_boxes = [font.getbbox(line) for line in lines]
    line_widths = [
        (b[2] - b[0]) + max(0, len(line) - 1) * letter_spacing
        for line, b in zip(lines, line_boxes)
    ]
    line_heights = [b[3] - b[1] for b in line_boxes]

    max_w = max(line_widths) if line_widths else 0
    line_gap = int(current_font_size * 0.35)
    total_h = sum(line_heights) + line_gap * (len(lines) - 1)

    y0 = int(height * base_y_ratio - total_h / 2 + drift_y)

    shadow_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    glow_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    stroke_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    fill_mask = Image.new("L", (width, height), 0)
    highlight_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))

    shadow_draw = ImageDraw.Draw(shadow_layer)
    glow_draw = ImageDraw.Draw(glow_layer)
    stroke_draw = ImageDraw.Draw(stroke_layer)
    mask_draw = ImageDraw.Draw(fill_mask)
    hi_draw = ImageDraw.Draw(highlight_layer)

    y = y0
    for idx, line in enumerate(lines):
        bbox = font.getbbox(line)
        text_h = bbox[3] - bbox[1]
        line_w = line_widths[idx]
        x = int((width - line_w) / 2)

        cursor_x = x
        for ch in line:
            cb = font.getbbox(ch)
            cw = cb[2] - cb[0]

            shadow_draw.text(
                (cursor_x + 2, y + 4),
                ch,
                font=font,
                fill=(8, 24, 28, int(135 * alpha_factor))
            )

            glow_draw.text(
                (cursor_x, y),
                ch,
                font=font,
                fill=(70, 190, 185, int(34 * alpha_factor))
            )

            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    stroke_draw.text(
                        (cursor_x + dx, y + dy),
                        ch,
                        font=font,
                        fill=(120, 185, 190, int(36 * alpha_factor))
                    )

            mask_draw.text(
                (cursor_x, y),
                ch,
                font=font,
                fill=int(255 * alpha_factor)
            )

            hi_draw.text(
                (cursor_x, y - 1),
                ch,
                font=font,
                fill=(245, 255, 252, int(34 * alpha_factor))
            )

            cursor_x += cw + letter_spacing

        y += text_h + line_gap

    blur_base = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    blur_base = Image.alpha_composite(blur_base, shadow_layer)
    blur_base = Image.alpha_composite(blur_base, glow_layer)
    blurred_layer = blur_base.filter(ImageFilter.GaussianBlur(radius=blur_radius))

    gradient = make_vertical_gradient(
        (width, height),
        top_color=(238, 248, 245, int(255 * alpha_factor)),
        bottom_color=(176, 210, 208, int(255 * alpha_factor)),
    )

    fill_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    fill_layer.paste(gradient, (0, 0), fill_mask)

    text_rgba = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    text_rgba = Image.alpha_composite(text_rgba, blurred_layer)
    text_rgba = Image.alpha_composite(text_rgba, stroke_layer)
    text_rgba = Image.alpha_composite(text_rgba, fill_layer)
    text_rgba = Image.alpha_composite(text_rgba, highlight_layer)

    return text_rgba


# =========================
# Pipeline
# =========================
def build_text_frame_cache(
    texts,
    interval,
    fps,
    width,
    height,
    font_path,
    font_size,
    base_y_ratio=0.5,
    letter_spacing=6,
    blur_radius=6,
):
    frames_per_text = max(1, int(round(interval * fps)))
    cache = []

    for text in texts:
        text_frames = []
        for i in range(frames_per_text):
            progress = i / max(1, frames_per_text - 1)
            img = render_styled_text(
                canvas_size=(width, height),
                text=text,
                font_path=font_path,
                font_size=font_size,
                progress=progress,
                base_y_ratio=base_y_ratio,
                letter_spacing=letter_spacing,
                blur_radius=blur_radius,
            )
            text_frames.append(img)
        cache.append(text_frames)

    return cache, frames_per_text


def preprocess_bg_frame(frame: np.ndarray, width: int, height: int):
    bg_img = cover_resize_np(frame, width, height)
    bg_img = bg_img.filter(ImageFilter.GaussianBlur(radius=2))
    overlay = Image.new("RGBA", (width, height), (8, 28, 32, 68))
    bg_img = Image.alpha_composite(bg_img, overlay)
    return bg_img


def compose_frame(bg_rgba: Image.Image, text_rgba: Image.Image | None):
    if text_rgba is not None:
        frame = Image.alpha_composite(bg_rgba, text_rgba)
    else:
        frame = bg_rgba
    return np.array(frame.convert("RGB"))


def run_text_video_pipeline(
    texts,
    interval,
    bg_video_path,
    output_path="text_intro.mp4",
    font_path=r"C:/Windows/Fonts/simsun.ttc",
    font_size=120,
    fps=30,
    width=1920,
    height=1080,
    keep_bg_audio=False,
    letter_spacing=6,
    base_y_ratio=0.5,
    text_blur_radius=6,
    min_duration=10.0,
):
    bg_clip = VideoFileClip(bg_video_path)

    text_duration = len(texts) * interval
    total_duration = max(text_duration, float(min_duration))

    text_cache, frames_per_text = build_text_frame_cache(
        texts=texts,
        interval=interval,
        fps=fps,
        width=width,
        height=height,
        font_path=font_path,
        font_size=font_size,
        base_y_ratio=base_y_ratio,
        letter_spacing=letter_spacing,
        blur_radius=text_blur_radius,
    )

    def make_frame(t):
        bg_t = t % bg_clip.duration
        bg_frame = bg_clip.get_frame(bg_t)
        bg_rgba = preprocess_bg_frame(bg_frame, width, height)

        # 文字时间已经结束，只保留背景
        if t >= text_duration or len(texts) == 0:
            return compose_frame(bg_rgba, None)

        text_idx = min(int(t // interval), len(texts) - 1)
        local_t = t - text_idx * interval
        local_frame_idx = min(int(local_t * fps), frames_per_text - 1)

        text_rgba = text_cache[text_idx][local_frame_idx]
        return compose_frame(bg_rgba, text_rgba)

    final_clip = VideoClip(make_frame, duration=total_duration)

    if keep_bg_audio and bg_clip.audio is not None:
        audio = bg_clip.audio.audio_loop(duration=total_duration)
        final_clip = final_clip.set_audio(audio)

    final_clip.write_videofile(
        output_path,
        fps=fps,
        codec="libx264",
        audio_codec="aac",
    )

    bg_clip.close()
    final_clip.close()
    return output_path


# =========================
# Example
# =========================
if __name__ == "__main__":
    texts = [
        "后来我才明白",
        "有些话不是忘了说",
        "只是没有机会再说了",
        "风停了，你也不在了"
    ]

    result = run_text_video_pipeline(
        texts=texts,
        interval=2.0,
        bg_video_path=r"D:\video\video\灵梦.mp4",
        output_path="sad_text_intro.mp4",
        font_path=r"C:\Windows\Fonts\simsun.ttc",
        font_size=128,
        fps=30,
        width=1920,
        height=1080,
        keep_bg_audio=True,
        letter_spacing=6,
        base_y_ratio=0.5,
        text_blur_radius=6,
        min_duration=10.0,
    )

    print("输出文件：", result)