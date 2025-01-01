"""Tests admin.keep.alive type, version 000"""

from named_types import AdminKeepAlive


def test_admin_keep_alive_generated() -> None:
    d = {
        "TypeName": "admin.keepalive",
        "Version": "001",
    }

    d2 = AdminKeepAlive.model_validate(d).model_dump(exclude_none=True)

    assert d2 == d
