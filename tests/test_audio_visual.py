from PIL import Image

from pyJianYingDraft.util.audio_visual.interface import AudioVisual


class DummyVisual(AudioVisual):
    def draw_frame(self, v: float, t: float, size):
        return Image.new("RGBA", size, (255, 255, 255, 255))


def test_make_video_uses_generated_frames(monkeypatch, tmp_path):
    visual = DummyVisual(fps=2)
    visual.tempfile_dir = str(tmp_path)

    monkeypatch.setattr(visual, "load_audio_values", lambda _: [0.1, 0.2, 0.3])

    class DummyStdin:
        def __init__(self):
            self.writes = 0

        def write(self, _):
            self.writes += 1

        def close(self):
            return None

    class DummyProc:
        def __init__(self):
            self.stdin = DummyStdin()

        def wait(self):
            return 0

    dummy_proc = DummyProc()
    monkeypatch.setattr("subprocess.Popen", lambda *args, **kwargs: dummy_proc)

    out = visual.make_video("fake.mp3")
    assert out.endswith("out.mov")
    assert dummy_proc.stdin.writes == 3
