import os
import ffmpeg


FFMPEG_EXE = r"D:\video\ffmpeg-2026-04-01-git-eedf8f0165-full_build\bin\ffmpeg.exe"
FFPROBE_EXE = r"D:\video\ffmpeg-2026-04-01-git-eedf8f0165-full_build\bin\ffprobe.exe"


def _get_video_duration(path: str) -> float:
    try:
        probe = ffmpeg.probe(path, cmd=FFPROBE_EXE)
    except ffmpeg.Error as e:
        print("FFPROBE STDERR:")
        print(e.stderr.decode("utf-8", errors="ignore") if e.stderr else "")
        raise

    # 先取 format.duration，拿不到再从 video stream 里找
    fmt = probe.get("format", {})
    if "duration" in fmt and fmt["duration"] not in (None, ""):
        return float(fmt["duration"])

    for s in probe.get("streams", []):
        if s.get("codec_type") == "video" and s.get("duration") not in (None, ""):
            return float(s["duration"])

    raise RuntimeError(f"Cannot determine duration: {path}")


def apply_video_mask(
    source_path: str,
    mask_path: str,
    output_path: str,
    mode: str = "alpha_from_luma",
    keep_audio: bool = False,
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
        source_probe = ffmpeg.probe(source_path, cmd=FFPROBE_EXE)
        mask_probe = ffmpeg.probe(mask_path, cmd=FFPROBE_EXE)
    except ffmpeg.Error as e:
        print("FFPROBE STDERR:")
        print(e.stderr.decode("utf-8", errors="ignore") if e.stderr else "")
        raise

    source_video_stream = next(
        s for s in source_probe["streams"] if s["codec_type"] == "video"
    )
    width = int(source_video_stream["width"])
    height = int(source_video_stream["height"])

    source_duration = _get_video_duration(source_path)
    mask_duration = _get_video_duration(mask_path)

    # 你的要求：mask 比 source 长，直接报错
    if mask_duration > source_duration:
        raise ValueError(
            f"mask duration ({mask_duration:.3f}s) is longer than source duration ({source_duration:.3f}s)"
        )

    source = ffmpeg.input(source_path)
    mask = ffmpeg.input(mask_path)

    # source 按 mask 时长截断
    source_v = (
        source.video
        .filter("trim", start=0, duration=mask_duration)
        .filter("setpts", "PTS-STARTPTS")
        .filter("format", "rgba")
    )

    mask_v = (
        mask.video
        .filter("trim", start=0, duration=mask_duration)
        .filter("setpts", "PTS-STARTPTS")
        .filter("scale", width, height)
        .filter("format", "gray")
    )

    if mode == "alpha_from_luma":
        alpha_src = mask_v
    elif mode == "alpha_from_luma_invert":
        alpha_src = mask_v.filter("negate")
    else:
        raise ValueError("mode must be 'alpha_from_luma' or 'alpha_from_luma_invert'")

    masked = ffmpeg.filter([source_v, alpha_src], "alphamerge")

    out_kwargs = {
        "vcodec": "qtrle",
        "pix_fmt": "argb",
    }

    if keep_audio:
        # 音频也按 mask 时长截断
        source_a = (
            source.audio
            .filter("atrim", start=0, duration=mask_duration)
            .filter("asetpts", "PTS-STARTPTS")
        )

        stream = ffmpeg.output(
            masked,
            source_a,
            output_path,
            **out_kwargs,
        )
    else:
        stream = ffmpeg.output(
            masked,
            output_path,
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