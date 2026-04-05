import importlib.util
import pathlib


spec = importlib.util.spec_from_file_location("demo_test_module", pathlib.Path(__file__).resolve().parents[1] / "test.py")
demo_module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(demo_module)
DemoScriptFactory = demo_module.DemoScriptFactory


def test_short_name_keeps_compatibility():
    assert DemoScriptFactory.short_name("abc.mp3") == "《abc》"
    assert DemoScriptFactory.short_name("abcdefghijklmn.mp3", max_len=9).startswith("《abcdef")
