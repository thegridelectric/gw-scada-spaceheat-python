import json
import shutil
from pathlib import Path
from typing import Optional
from typing import Union

import gwproto.messages
import pendulum
from gwproto.messages import ProblemEvent
from result import Result

from actors2.config import ScadaSettings
from gwproactor.persister import FileExistedWarning
from gwproactor.persister import FileMissing
from gwproactor.persister import FileMissingWarning
from gwproactor.persister import PersisterError
from gwproactor.persister import PersisterException
from gwproactor.persister import PersisterWarning
from gwproactor.persister import ReindexError
from gwproactor.persister import TimedRollingFilePersister
from gwproactor.persister import TrimFailed
from gwproactor.persister import UIDExistedWarning
from gwproactor.persister import UIDMissingWarning
from problems import Problems


def test_problems():

    p = Problems()
    assert not p
    assert not str(p)
    assert repr(p) == str(p)
    assert p.max_problems == Problems.MAX_PROBLEMS
    p.add_error(PersisterError(uid="1"))
    assert p
    assert len(p.errors) == 1
    assert len(p.warnings) == 0
    p.add_warning(PersisterWarning(uid="2"))
    assert p
    assert len(p.errors) == 1
    assert len(p.warnings) == 1
    assert repr(p) == str(p)
    p2 = Problems(
        errors=[PersisterError(uid="3"), PersisterError(uid="4")],
        warnings=[PersisterWarning(uid="5"), PersisterWarning(uid="6")],
        max_problems=4,
    )
    assert p2
    assert len(p2.errors) == 2
    assert len(p2.warnings) == 2
    p2.add_problems(p)
    assert len(p2.errors) == 3
    assert len(p2.warnings) == 3
    assert str(p2)
    p3 = Problems(
        errors=[PersisterError(uid="7"), PersisterError(uid="8")],
        warnings=[PersisterWarning(uid="9"), PersisterWarning(uid="10")],
    )
    p2.add_problems(p3)
    assert len(p2.errors) == 4
    assert len(p2.warnings) == 4
    p2.add_error(PersisterError(uid="11"))
    p2.add_warning(PersisterWarning(uid="12"))
    assert len(p2.errors) == 4
    assert len(p2.warnings) == 4
    assert [int(entry.uid) for entry in p2.errors] == [3, 4, 1, 7]  # noqa: type
    assert [int(entry.uid) for entry in p2.warnings] == [5, 6, 2, 9]  # noqa: type
    assert str(p2)


def test_persister_exception():
    e = PersisterException("foo")
    assert str(e)
    assert e.uid == ""
    assert e.path is None

    e = PersisterException("foo", "bar")
    assert str(e)
    assert e.uid == "bar"
    assert e.path is None

    e = PersisterException(uid="bar", path=Path("."))
    assert str(e)
    assert e.uid == "bar"
    assert e.path == Path(".")


def assert_contents(
    p: TimedRollingFilePersister,
    uids: Optional[list] = None,
    exp_paths: Optional[list] = None,
    nearby_days: bool = True,
    possible_days: Optional[list[pendulum.datetime]] = None,
    exact_days: Optional[list[pendulum.datetime]] = None,
    num_pending: Optional[int] = None,
    curr_bytes: Optional[int] = None,
    curr_dir: Optional[Union[str, Path]] = None,
    check_index: bool = True,
    max_bytes: Optional[int] = None,
):
    assert p.num_pending == len(p.pending())
    if num_pending is not None:
        assert p.num_pending == num_pending
    if curr_bytes is not None:
        assert p.curr_bytes == curr_bytes
    if curr_dir is None and exact_days:
        curr_dir = exact_days[-1].isoformat()
    if curr_dir is not None:
        if isinstance(curr_dir, str):
            assert p.curr_dir.name == curr_dir
        else:
            assert p.curr_dir == curr_dir
    if max_bytes is not None:
        assert p.max_bytes == max_bytes
    if uids is not None:
        str_uids = [str(uid) for uid in uids]
        assert p.pending() == str_uids
        assert p.num_pending == len(str_uids)
        for str_uid in str_uids:
            assert str_uid in p
    got_paths = [p.get_path(uid) for uid in p.pending()]
    if exp_paths is not None:
        assert exp_paths == got_paths
    if nearby_days:
        if possible_days is None:
            possible_days = []
        possible_days.extend([pendulum.yesterday("utc"), pendulum.today("utc"), pendulum.tomorrow("utc")])
    if exact_days is not None:
        possible_days = exact_days
    if possible_days is not None and got_paths:
        possible_days_str_list = [dt.isoformat() for dt in possible_days]
        got_day_strs_list = [path.parent.name for path in got_paths]
        if exact_days:
            assert possible_days_str_list == got_day_strs_list
            assert p.curr_dir.name == possible_days_str_list[-1]
            dirs_exp = sorted(set(possible_days_str_list))
            dirs_got = sorted([path.name for path in p.base_dir.iterdir() if path.is_dir()])
            assert dirs_exp == dirs_got
        else:
            possible_day_strs = set(possible_days_str_list)
            got_day_strs = set(got_day_strs_list)
            assert got_day_strs.issubset(possible_day_strs), f"\ngot: {got_day_strs}\nexp: {possible_day_strs}"
            assert p.curr_dir.name in possible_days_str_list
    if check_index:
        p2 = TimedRollingFilePersister(
            base_dir=p.base_dir,
            max_bytes=p.max_bytes,
        )
        if p.num_pending == 0:
            assert p.curr_bytes == 0
        assert p.pending() == p2.pending()
        # noinspection PyProtectedMember
        assert p.pending() == list(p._pending.keys())
        # noinspection PyProtectedMember
        assert got_paths == list(p._pending.values())
        for uid, path in zip(p.pending(), got_paths):
            assert path.exists()
            assert uid in str(path.name)


def test_persister_happy_path(tmp_path):
    settings = ScadaSettings()
    settings.paths.mkdirs()
    event = ProblemEvent(
        Src="foo",
        ProblemType=gwproto.messages.Problems.error,
        Summary="Problems, I've got a few",
        Details="Too numerous to name"
    )
    event_bytes = event.json().encode()

    # empty persister
    persister = TimedRollingFilePersister(settings. paths.event_dir)
    assert persister.reindex().is_ok()
    assert persister.get_path("foo") is None
    assert_contents(
        persister,
        num_pending=0,
        max_bytes=TimedRollingFilePersister.DEFAULT_MAX_BYTES,
        curr_bytes=0,
    )

    # add one
    result = persister.persist(event.MessageId, event_bytes)
    assert result.is_ok()
    assert_contents(
        persister,
        uids=[event.MessageId],
        num_pending=1,
        curr_bytes=len(event_bytes),
    )

    # retrieve
    retrieved = persister.retrieve(event.MessageId)
    assert retrieved.is_ok(), str(retrieved)
    assert retrieved.value == event_bytes

    # deserialize
    loaded = json.loads(retrieved.value.decode("utf-8"))
    assert loaded == json.loads(event.json())
    loaded_event = ProblemEvent.parse_raw(retrieved.value)
    assert loaded_event == event

    # add another
    event2 = ProblemEvent(Src="foo", Summary="maybe not great", ProblemType=gwproto.messages.Problems.warning)
    event2_bytes = event2.json().encode()
    result = persister.persist(event2.MessageId, event2.json().encode())
    assert result.is_ok()
    assert_contents(
        persister,
        uids=[event.MessageId, event2.MessageId],
        num_pending=2,
        curr_bytes=len(event_bytes) + len(event2_bytes),
    )

    # reindex
    assert persister.reindex().is_ok()
    assert_contents(
        persister,
        uids=[event.MessageId, event2.MessageId],
        num_pending=2,
        curr_bytes=len(event_bytes) + len(event2_bytes),
    )

    # clear second one
    cleared = persister.clear(event2.MessageId)
    assert cleared.is_ok()
    assert event2.MessageId not in persister.pending()
    assert persister.get_path(event2.MessageId) is None
    assert_contents(
        persister,
        uids=[event.MessageId],
        num_pending=1,
        curr_bytes=len(event_bytes),
    )

    # clear first one
    old_path = persister.get_path(event.MessageId)
    assert old_path.exists()
    cleared = persister.clear(event.MessageId)
    assert cleared.is_ok()
    assert not old_path.exists()
    assert event.MessageId not in persister.pending()
    assert persister.get_path(event.MessageId) is None
    assert_contents(
        persister,
        num_pending=0,
        curr_bytes=0,
    )

    # reindex
    assert persister.reindex().is_ok()
    assert len(persister.pending()) == persister.num_pending == 0
    assert persister.curr_dir.name in [pendulum.today("utc").isoformat(), pendulum.yesterday("utc").isoformat()]
    assert persister.curr_bytes == 0
    assert_contents(
        persister,
        num_pending=0,
        curr_bytes=0,
    )


def test_persister_max_size():
    settings = ScadaSettings()
    settings.paths.mkdirs()
    event = ProblemEvent(
        MessageId=" 0",
        Src=".",
        ProblemType=gwproto.messages.Problems.error,
        Summary="0",
        Details="x" * 1024
    )

    def inc_event():
        event.MessageId = f"{int(event.MessageId) + 1:2d}"
    event_bytes = event.json().encode()
    num_events_supported = 4
    with pendulum.test(pendulum.today("utc")):

        # empty persister
        max_bytes = (num_events_supported + 1) * 1000
        p = TimedRollingFilePersister(settings. paths.event_dir, max_bytes=max_bytes)
        assert_contents(p, max_bytes=max_bytes, num_pending=0)

        # a few
        uids = []
        for i in range(1, num_events_supported + 1):
            inc_event()
            uids.append(event.MessageId)
            result = p.persist(event.MessageId, event.json().encode())
            assert result.is_ok(), str(result)
            assert_contents(p, num_pending=i, curr_bytes=i * len(event_bytes), uids=uids)

        # a few more - now size should not change
        for i in range(1, num_events_supported * 2):
            inc_event()
            uids.append(event.MessageId)
            uids = uids[1:]
            result = p.persist(event.MessageId, event.json().encode())
            assert result.is_ok(), str(result)
            assert_contents(
                p,
                num_pending=num_events_supported,
                curr_bytes=num_events_supported * len(event_bytes),
                uids=uids
            )

        # add a bigger item; more than one must be removed.
        inc_event()
        old_size = len(event_bytes)
        event.Details *= 2
        big_event_bytes = event.json().encode()
        exp_size = p.curr_bytes - (2 * old_size) + len(big_event_bytes)
        exp_pending = num_events_supported - 1
        uids.append(event.MessageId)
        uids = uids[2:]
        result = p.persist(event.MessageId, big_event_bytes)
        assert result.is_ok(), str(result)
        assert_contents(
            p,
            num_pending=exp_pending,
            curr_bytes=exp_size,
            uids=uids
        )

        # Cannot add one too large, state of persister doesn't change
        inc_event()
        event.Details = "." * (max_bytes + 1)
        result = p.persist(event.MessageId, event.json().encode())
        assert not result.is_ok()
        assert_contents(
            p,
            num_pending=exp_pending,
            curr_bytes=exp_size,
            uids=uids
        )


def test_persister_roll_day():
    settings = ScadaSettings()
    settings.paths.mkdirs()
    event = ProblemEvent(
        MessageId=" 0",
        Src=".",
        ProblemType=gwproto.messages.Problems.error,
        Summary="0",
        Details="x" * 1024
    )

    def inc_event():
        event.MessageId = f"{int(event.MessageId) + 1:2d}"
    uids = [event.MessageId]
    d1 = pendulum.today("utc")
    d2 = d1.add(days=1)
    d3 = d2.add(days=1)

    try:
        # d1
        pendulum.set_test_now(d1)
        exact_days = [d1]
        p = TimedRollingFilePersister(settings.paths.event_dir)
        assert_contents(p, num_pending=0, curr_dir=d1.isoformat())
        result = p.persist(event.MessageId, event.json().encode())
        assert result.is_ok()
        assert_contents(p, num_pending=1, uids=uids, exact_days=exact_days)
        assert p.get_path(event.MessageId).parent.name == exact_days[-1].isoformat()

        # d2
        pendulum.set_test_now(d2)
        exact_days.append(d2)
        inc_event()
        uids.append(event.MessageId)
        result = p.persist(event.MessageId, event.json().encode())
        assert result.is_ok()
        assert_contents(p, num_pending=2, uids=uids, exact_days=exact_days)
        assert p.get_path(event.MessageId).parent.name == exact_days[-1].isoformat()

        # d3
        pendulum.set_test_now(d3)
        exact_days.append(d3)
        inc_event()
        uids.append(event.MessageId)
        result = p.persist(event.MessageId, event.json().encode())
        assert result.is_ok()
        assert_contents(p, num_pending=3, uids=uids, exact_days=exact_days)
        assert p.get_path(event.MessageId).parent.name == exact_days[-1].isoformat()

        # d3 - add another
        exact_days.append(d3)
        inc_event()
        uids.append(event.MessageId)
        result = p.persist(event.MessageId, event.json().encode())
        assert result.is_ok()
        assert_contents(p, num_pending=4, uids=uids, exact_days=exact_days)
        assert p.get_path(event.MessageId).parent.name == exact_days[-1].isoformat()

        # verify first day directory is present
        uid = p.pending()[0]
        path = p.get_path(uid)
        day_dir = path.parent
        assert path.exists()
        assert day_dir.exists()

        # clear the first entry from d1, verify d1 is gone
        result = p.clear(uid)
        assert result.ok()
        assert not path.exists()
        assert not day_dir.exists()
        uids = uids[1:]
        exact_days = exact_days[1:]
        assert_contents(p, num_pending=3, uids=uids, exact_days=exact_days)

        # Repeat with d2.
        # Clear the first entry from d2, verify d2 is gone
        uid = p.pending()[0]
        path = p.get_path(uid)
        day_dir = path.parent
        assert path.exists()
        assert day_dir.exists()
        result = p.clear(uid)
        assert result.ok()
        assert not path.exists()
        assert not day_dir.exists()
        uids = uids[1:]
        exact_days = exact_days[1:]
        assert_contents(p, num_pending=2, uids=uids, exact_days=exact_days)

        # clear first entry from third day, verify third day dir still exists
        uid = p.pending()[0]
        path = p.get_path(uid)
        day_dir = path.parent
        assert path.exists()
        assert day_dir.exists()
        result = p.clear(uid)
        assert result.ok()
        assert not path.exists()
        assert day_dir.exists()
        uids = uids[1:]
        assert_contents(p, num_pending=1, uids=uids, exact_days=exact_days[1:])

        uid = p.pending()[0]
        path = p.get_path(uid)
        assert path.exists()
        assert path.parent == day_dir
        result = p.clear(uid)
        assert result.ok()
        assert not path.exists()
        assert not day_dir.exists()
        assert_contents(p, num_pending=0)

    finally:
        pendulum.set_test_now()


def test_persister_size_and_roll():
    settings = ScadaSettings()
    settings.paths.mkdirs()
    uidi = 1

    def inc_uid() -> str:
        nonlocal uidi
        uid_ = f"{uidi:2d}"
        uidi += 1
        return uid_

    uids = []
    d1 = pendulum.today("utc")
    d2 = d1.add(days=1)
    d3 = d2.add(days=1)
    d4 = d3.add(days=1)
    d5 = d4.add(days=1)

    num_supported = 10
    packet_size = 1000
    max_size = num_supported * packet_size
    buf = ("." * packet_size).encode()

    try:
        # d1, add two
        exact_days = []
        pendulum.set_test_now(d1)
        p = TimedRollingFilePersister(settings.paths.event_dir, max_bytes=max_size)
        assert_contents(p, num_pending=0, curr_dir=d1.isoformat(), max_bytes=max_size)
        for i in range(1, 3):
            uids.append(inc_uid())
            exact_days.append(d1)
            result = p.persist(uids[-1], buf)
            assert result.is_ok()
            assert_contents(p, num_pending=i, curr_bytes=packet_size * i, uids=uids, exact_days=exact_days)
            assert p.get_path(uids[-1]).parent.name == exact_days[-1].isoformat()

        # d2, add another two
        pendulum.set_test_now(d2)
        for i in range(3, 5):
            uids.append(inc_uid())
            exact_days.append(d2)
            result = p.persist(uids[-1], buf)
            assert result.is_ok(), str(result)
            assert_contents(p, num_pending=i, curr_bytes=packet_size * i, uids=uids, exact_days=exact_days)
            assert p.get_path(uids[-1]).parent.name == exact_days[-1].isoformat()

        # d3, add three
        pendulum.set_test_now(d3)
        for i in range(5, 8):
            uids.append(inc_uid())
            exact_days.append(d3)
            result = p.persist(uids[-1], buf)
            assert result.is_ok()
            assert_contents(p, num_pending=i, curr_bytes=packet_size * i, uids=uids, exact_days=exact_days)
            assert p.get_path(uids[-1]).parent.name == exact_days[-1].isoformat()

        # d4, add two
        pendulum.set_test_now(d4)
        for i in range(8, 10):
            uids.append(inc_uid())
            exact_days.append(d4)
            result = p.persist(uids[-1], buf)
            assert result.is_ok()
            assert_contents(p, num_pending=i, curr_bytes=packet_size * i, uids=uids, exact_days=exact_days)
            assert p.get_path(uids[-1]).parent.name == exact_days[-1].isoformat()

        # d5, add 1
        pendulum.set_test_now(d5)
        for i in range(10, 11):
            uids.append(inc_uid())
            exact_days.append(d5)
            result = p.persist(uids[-1], buf)
            assert result.is_ok()
            assert_contents(p, num_pending=i, curr_bytes=packet_size * i, uids=uids, exact_days=exact_days)
            assert p.get_path(uids[-1]).parent.name == exact_days[-1].isoformat()

        assert p.curr_bytes == p.max_bytes

        # add one more, which keeps size the same but removes first entry. First day dir should remain.
        uid = p.pending()[0]
        path = p.get_path(uid)
        day_dir = path.parent
        assert path.exists()
        assert day_dir.exists()

        uids.append(inc_uid())
        uids = uids[1:]
        exact_days.append(d5)
        exact_days = exact_days[1:]
        result = p.persist(uids[-1], buf)
        assert result.is_ok()
        assert_contents(p, num_pending=10, curr_bytes=max_size, uids=uids, exact_days=exact_days)
        assert p.get_path(uids[-1]).parent.name == exact_days[-1].isoformat()
        assert not path.exists()
        assert day_dir.exists()

        # add one more, which now should first day dir to be gone.
        uid = p.pending()[0]
        path = p.get_path(uid)
        day_dir = path.parent
        assert path.exists()
        assert day_dir.exists()
        uids.append(inc_uid())
        uids = uids[1:]
        exact_days.append(d5)
        exact_days = exact_days[1:]
        result = p.persist(uids[-1], buf)
        assert result.is_ok()
        assert_contents(p, num_pending=10, curr_bytes=max_size, uids=uids, exact_days=exact_days)
        assert p.get_path(uids[-1]).parent.name == exact_days[-1].isoformat()
        assert not path.exists()
        assert not day_dir.exists()

        # add a large one, 2x size, which now should remove two entries and second day
        uid0 = p.pending()[0]
        path0 = p.get_path(uid0)
        uid1 = p.pending()[1]
        path1 = p.get_path(uid1)
        day_dir = path0.parent
        assert path1.parent == day_dir
        assert path0.exists()
        assert path1.exists()
        assert day_dir.exists()
        uids.append(inc_uid())
        uids = uids[2:]
        exact_days.append(d5)
        exact_days = exact_days[2:]
        result = p.persist(uids[-1], buf * 2)
        assert result.is_ok()
        assert_contents(p, num_pending=9, curr_bytes=max_size, uids=uids, exact_days=exact_days)
        assert p.get_path(uids[-1]).parent.name == exact_days[-1].isoformat()
        assert not path0.exists()
        assert not path1.exists()
        assert not day_dir.exists()

        # add a large one, 4x size, which now should third day and one entry of fourth day
        removed_uids = p.pending()[:4]
        paths = [p.get_path(uid) for uid in removed_uids]
        day_dirs = [path.parent for path in paths]
        assert all([path.exists() for path in paths])
        assert all([day_dir.exists() for day_dir in day_dirs])
        uids.append(inc_uid())
        uids = uids[4:]
        exact_days.append(d5)
        exact_days = exact_days[4:]
        result = p.persist(uids[-1], buf * 4)
        assert result.is_ok()
        assert_contents(p, num_pending=6, curr_bytes=max_size, uids=uids, exact_days=exact_days)
        assert all([not path.exists() for path in paths])
        assert not day_dirs[0].exists()
        assert not day_dirs[1].exists()
        assert not day_dirs[2].exists()
        assert day_dirs[3].exists()

        # clear last entry in fourth day
        uid = p.pending()[0]
        path = p.get_path(uid)
        day_dir = path.parent
        assert path.exists()
        assert day_dir.exists()
        uids = uids[1:]
        exact_days = exact_days[1:]
        exp_size = max_size - packet_size
        result = p.clear(uid)
        assert result.is_ok()
        assert_contents(p, num_pending=5, curr_bytes=exp_size, uids=uids, exact_days=exact_days)
        assert p.get_path(uids[-1]).parent.name == exact_days[-1].isoformat()
        assert not path.exists()
        assert not day_dir.exists()

        # clear the rest
        num_pending = p.num_pending
        while p.num_pending:
            uid = p.pending()[0]
            path = p.get_path(uid)
            path_size = path.stat().st_size
            assert path.parent == p.curr_dir
            result = p.clear(uid)
            assert result.is_ok()
            num_pending -= 1
            uids = uids[1:]
            exact_days = exact_days[1:]
            exp_size -= path_size
            assert_contents(p, num_pending=num_pending, curr_bytes=exp_size, uids=uids, exact_days=exact_days)
            assert not path.exists()
            if p.num_pending:
                assert path.parent.exists()
            else:
                assert not path.parent.exists()
    finally:
        pendulum.set_test_now()


def test_persister_indexing():
    settings = ScadaSettings()
    settings.paths.mkdirs()
    uidi = 1

    def inc_uid() -> str:
        nonlocal uidi
        uid_ = f"{uidi:2d}"
        uidi += 1
        return uid_
    buf = ("." * 100).encode()
    d1 = pendulum.today("utc")
    d2 = d1.add(days=1)
    d3 = d2.add(days=1)
    d4 = d3.add(days=1)

    try:
        pendulum.set_test_now(d1)
        p = TimedRollingFilePersister(settings.paths.event_dir)
        p.persist(inc_uid(), buf)
        p.persist(inc_uid(), buf)

        pendulum.set_test_now(d2)
        p.persist(inc_uid(), buf)
        p.persist(inc_uid(), buf)

        pendulum.set_test_now(d3)
        p.persist(inc_uid(), buf)
        p.persist(inc_uid(), buf)

        pendulum.set_test_now(d4)
        p.persist(inc_uid(), buf)
        p.persist(inc_uid(), buf)

        index = dict(p._pending)
        p = TimedRollingFilePersister(settings.paths.event_dir)
        assert p._pending == index

        # removed dir
        shutil.rmtree(p.get_path(p.pending()[0]).parent, ignore_errors=True)
        index.pop(p.pending()[0])
        index.pop(p.pending()[1])
        # removed file
        p.get_path(p.pending()[2]).unlink()
        index.pop(p.pending()[2])
        # removed all files in dir, left dir
        p.get_path(p.pending()[4]).unlink()
        index.pop(p.pending()[4])
        p.get_path(p.pending()[5]).unlink()
        index.pop(p.pending()[5])
        p6 = p.get_path(p.pending()[6])
        p6_dir = p6.parent
        # invalid file - rgx failure
        shutil.copy(p6, p6_dir / (p6.name + "x"))
        # invalid file - invalid date
        shutil.copy(p6, p6_dir / ("x" + p6.name))
        p = TimedRollingFilePersister(settings.paths.event_dir)
        assert p._pending == index

    finally:
        pendulum.set_test_now()


def test_persister_problems():
    settings = ScadaSettings()
    settings.paths.mkdirs()
    uidi = 1

    def inc_uid() -> str:
        nonlocal uidi
        uid_ = f"{uidi:2d}"
        uidi += 1
        return uid_
    uids = []
    exact_days = []
    buf = ("." * 100).encode()
    d1 = pendulum.today("utc")

    try:
        pendulum.set_test_now(d1)
        p = TimedRollingFilePersister(settings.paths.event_dir)
        uids.append(inc_uid())
        exact_days.append(d1)

        # persist, uid exists
        result = p.persist(uids[-1], buf)
        assert result.is_ok()
        assert_contents(p, uids=uids, num_pending=1, curr_bytes=len(buf), exact_days=exact_days)
        result = p.persist(uids[-1], buf)
        assert not result.is_ok()
        problems = result.err()
        assert len(problems.errors) == 0
        assert len(problems.warnings) == 2
        assert isinstance(problems.warnings[0], UIDExistedWarning)
        assert isinstance(problems.warnings[1], FileExistedWarning)
        p.get_path(uids[-1]).unlink()
        result = p.persist(uids[-1], buf)
        problems = result.err()
        assert not result.is_ok()
        assert len(problems.errors) == 0
        assert len(problems.warnings) == 2
        assert isinstance(problems.warnings[0], UIDExistedWarning)
        assert isinstance(problems.warnings[1], FileMissingWarning)

        # persist, unexpected error
        class BrokenRoller(TimedRollingFilePersister):
            def _roll_curr_dir(self):
                raise ValueError("whoops")
        broken = BrokenRoller(settings.paths.event_dir)
        problems = broken.persist("bla", buf).unwrap_err()
        assert len(problems.errors) == 2
        assert len(problems.warnings) == 0
        assert isinstance(problems.errors[0], ValueError)
        assert isinstance(problems.errors[1], PersisterError)

        # _trim_old_storage, clear exception
        class BrokenRoller2(TimedRollingFilePersister):
            def clear(self, uid: str) -> Result[bool, Problems]:
                raise ValueError("arg")
        p = BrokenRoller2(settings.paths.event_dir, max_bytes=len(buf) + 50)
        problems = p.persist("xxxbla", buf).unwrap_err()
        assert len(problems.errors) == 3
        assert len(problems.warnings) == 0
        assert isinstance(problems.errors[0], ValueError)
        assert isinstance(problems.errors[1], PersisterError)
        assert isinstance(problems.errors[2], TrimFailed)

        # _trim_old_storage, clear error, file missing
        p = TimedRollingFilePersister(settings.paths.event_dir, max_bytes=len(buf) + 50)
        p.get_path(uids[-1]).unlink()
        problems = p.persist("xxxbla", buf).unwrap_err()
        assert len(problems.errors) == 0
        assert len(problems.warnings) == 1
        assert isinstance(problems.warnings[0], FileMissingWarning)

        # clear, uid missing
        problems = p.clear("foo").unwrap_err()
        assert len(problems.errors) == 0
        assert len(problems.warnings) == 1
        assert isinstance(problems.warnings[0], UIDMissingWarning)

        # retrieve, file missing
        p.persist(uids[-1], buf).expect("")
        p.get_path(uids[-1]).unlink()
        problems = p.retrieve(uids[-1]).unwrap_err()
        assert len(problems.errors) == 1
        assert len(problems.warnings) == 0
        assert isinstance(problems.errors[0], FileMissing)

        # reindex, _persisted_item_from_file_path exception
        shutil.rmtree(p.base_dir)
        settings.paths.mkdirs()
        p = TimedRollingFilePersister(settings.paths.event_dir, max_bytes=len(buf) + 50)
        p.persist(uids[-1], buf).unwrap()

        class BrokenRoller3(TimedRollingFilePersister):
            @classmethod
            def _persisted_item_from_file_path(cls, filepath: Path):
                raise ValueError("arg")
        p = BrokenRoller3(settings.paths.event_dir, max_bytes=len(buf) + 50)
        problems = p.reindex().unwrap_err()
        assert len(problems.errors) == 2
        assert len(problems.warnings) == 0
        assert isinstance(problems.errors[0], ValueError)
        assert isinstance(problems.errors[1], ReindexError)

        # reindex, _is_iso_parseable exception
        class BrokenRoller4(TimedRollingFilePersister):
            @classmethod
            def _is_iso_parseable(cls, s: str | Path) -> bool:
                raise ValueError("arg")
        p = BrokenRoller4(settings.paths.event_dir, max_bytes=len(buf) + 50)
        problems = p.reindex().unwrap_err()
        assert len(problems.errors) == 2
        assert len(problems.warnings) == 0
        assert isinstance(problems.errors[0], ValueError)
        assert isinstance(problems.errors[1], ReindexError)

    finally:
        pendulum.set_test_now()
