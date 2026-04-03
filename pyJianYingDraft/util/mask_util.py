import os
import ffmpeg


FFMPEG_EXE = r"D:\video\ffmpeg-2026-04-01-git-eedf8f0165-full_build\bin\ffmpeg.exe"
FFPROBE_EXE = r"D:\video\ffmpeg-2026-04-01-git-eedf8f0165-full_build\bin\ffprobe.exe"





def apply_video_mask(
    source_path: str,
    mask_path: str,
    output_path: str,
    mode: str = "alpha_from_luma",
    keep_audio: bool = True,
    duration: int = 0
) -> str:
    if not os.path.exists(source_path):
        raise FileNotFoundError(f"source not found: {source_path}")
    if not os.path.exists(mask_path):
        raise FileNotFoundError(f"mask not found: {mask_path}")

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    if not output_path.lower().endswith(".mov"):
        raise ValueError("output_path should use .mov when preserving alpha, e.g. output.mov")

    try:
        probe = ffmpeg.probe(source_path, cmd=FFPROBE_EXE)
    except ffmpeg.Error as e:
        print("FFPROBE STDERR:")
        print(e.stderr.decode("utf-8", errors="ignore") if e.stderr else "")
        raise

    source_video_stream = next(s for s in probe["streams"] if s["codec_type"] == "video")
    width = int(source_video_stream["width"])
    height = int(source_video_stream["height"])

    source = ffmpeg.input(source_path,t=duration)

    mask_ext = os.path.splitext(mask_path)[1].lower()
    image_exts = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}
    if mask_ext in image_exts:
        mask = ffmpeg.input(mask_path, loop=1, framerate=30,t=duration)
    else:
        mask = ffmpeg.input(mask_path,t=duration)

    source_v = source.video.filter("format", "rgba")
    mask_v = mask.video

    mask_gray = (
        mask_v
        .filter("scale", width, height)
        .filter("format", "gray")
    )

    if mode == "alpha_from_luma":
        alpha_src = mask_gray
    elif mode == "alpha_from_luma_invert":
        alpha_src = mask_gray.filter("negate")
    else:
        raise ValueError("mode must be 'alpha_from_luma' or 'alpha_from_luma_invert'")

    masked = ffmpeg.filter([source_v, alpha_src], "alphamerge")

    out_kwargs = {
        "vcodec": "qtrle",
        "pix_fmt": "argb",
    }

    if keep_audio:
        stream = ffmpeg.output(
            masked,
            source.audio,
            output_path,
            shortest=None,
            **out_kwargs,
        )
    else:
        stream = ffmpeg.output(
            masked,
            output_path,
            shortest=None,
            **out_kwargs,
        )

    try:
        ffmpeg.run(
            stream.overwrite_output(),
            cmd=FFMPEG_EXE,
            capture_stdout=True,
            capture_stderr=True,
        )
    except ffmpeg.Error as e:
        stderr_text = e.stderr.decode("utf-8", errors="ignore") if e.stderr else ""
        stdout_text = e.stdout.decode("utf-8", errors="ignore") if e.stdout else ""

        raise RuntimeError(
            "\n========== FFMPEG STDOUT ==========\n"
            + stdout_text
            + "\n========== FFMPEG STDERR ==========\n"
            + stderr_text
            + "\n===================================\n"
        )

    return output_path