import os
import sys
import types

ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# 测试环境可能没有 moviepy，注入最小桩模块保证导入通过
if "moviepy" not in sys.modules:
    moviepy_stub = types.ModuleType("moviepy")

    class _AudioFileClip:
        def __init__(self, *_args, **_kwargs):
            pass

        def to_soundarray(self, fps=44100):
            return [[0.0], [0.0]]

        def close(self):
            return None

    class _VideoFileClip:
        def __init__(self, *_args, **_kwargs):
            pass

    class _VideoClip:
        def __init__(self, *_args, **_kwargs):
            pass

    moviepy_stub.AudioFileClip = _AudioFileClip
    moviepy_stub.VideoFileClip = _VideoFileClip
    moviepy_stub.VideoClip = _VideoClip
    sys.modules["moviepy"] = moviepy_stub

if "ffmpeg" not in sys.modules:
    ffmpeg_stub = types.ModuleType("ffmpeg")
    ffmpeg_stub.probe = lambda *args, **kwargs: {"streams": [], "format": {}}
    ffmpeg_stub.input = lambda *args, **kwargs: types.SimpleNamespace(video=None, audio=None)
    ffmpeg_stub.filter = lambda *args, **kwargs: None
    ffmpeg_stub.output = lambda *args, **kwargs: types.SimpleNamespace(overwrite_output=lambda: None)
    ffmpeg_stub.run = lambda *args, **kwargs: None
    ffmpeg_stub.Error = Exception
    sys.modules["ffmpeg"] = ffmpeg_stub
