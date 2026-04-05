from types import SimpleNamespace

from pyJianYingDraft.time_util import SEC
from pyJianYingDraft.util.intro_video.implementations.masked_text_intro import IntroVideoAssets, MaskedTextIntroVideo


class DummyScript:
    def __init__(self):
        self.tracks = []
        self.segments = []

    def add_track(self, track_type, track, relative_index=None):
        self.tracks.append((track_type, track, relative_index))

    def add_segment(self, segment, track):
        self.segments.append((segment, track))


def test_build_uses_microsecond_timerange(monkeypatch, tmp_path):
    script = DummyScript()
    assets = IntroVideoAssets(bg_video_path="bg.mp4", mask_dir=str(tmp_path), output_dir=str(tmp_path))

    (tmp_path / "mask.mov").write_bytes(b"1")
    monkeypatch.setattr(
        "pyJianYingDraft.util.intro_video.implementations.masked_text_intro.run_text_video_pipeline",
        lambda **kwargs: "intro.mp4",
    )
    monkeypatch.setattr(
        "pyJianYingDraft.util.intro_video.implementations.masked_text_intro.apply_video_mask",
        lambda *args, **kwargs: "masked.mov",
    )

    materials = {
        "intro.mp4": SimpleNamespace(duration=2 * SEC),
        "masked.mov": SimpleNamespace(duration=1 * SEC),
    }

    monkeypatch.setattr(
        "pyJianYingDraft.util.intro_video.implementations.masked_text_intro.draft.VideoMaterial",
        lambda p: materials[p],
    )

    def fake_segment(_, timerange, volume=0.0):
        return SimpleNamespace(timerange=timerange, volume=volume)

    monkeypatch.setattr(
        "pyJianYingDraft.util.intro_video.implementations.masked_text_intro.draft.VideoSegment",
        fake_segment,
    )

    builder = MaskedTextIntroVideo(script, assets)
    end_us = builder.build(start_time=0.5, track="intro", texts=["abc"])

    assert end_us == int(3.5 * SEC)
    assert script.segments[0][0].timerange.start == int(0.5 * SEC)
    assert script.segments[0][0].timerange.duration == 2 * SEC
    assert script.segments[1][0].timerange.start == int(2.5 * SEC)
