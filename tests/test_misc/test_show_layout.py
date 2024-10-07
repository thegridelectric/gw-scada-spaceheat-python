from pathlib import Path

import rich

import show_layout


def test_show_layout_on_test_layout():
    layout_path = Path(__file__).parent.parent / "config" / "hardware-layout.json"
    errors = show_layout.main(["-l", str(layout_path)])
    if errors:
        rich.print(errors)
    assert not errors
