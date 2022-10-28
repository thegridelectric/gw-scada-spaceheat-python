import json

from gwproto.messages import ProblemEvent
from gwproto.messages import Problems

from config import ScadaSettings
from proactor.persister import TimedRollingFilePersister


def test_persister(tmp_path):
    settings = ScadaSettings()
    settings.paths.mkdirs()
    persister = TimedRollingFilePersister(settings.paths.event_dir)
    assert not persister.pending()
    event = ProblemEvent(
        Src="foo",
        ProblemType=Problems.error,
        Summary="Problems, I've got a few",
        Details="Too numerous to name"
    )
    result = persister.persist(event.MessageId, event.json().encode())
    assert result.is_ok()
    retrieved = persister.retrieve(event.MessageId)
    assert retrieved.is_ok(), str(retrieved)
    loaded = json.loads(retrieved.value.decode("utf-8"))
    assert loaded == json.loads(event.json())
    loaded_event = ProblemEvent.parse_raw(retrieved.value)
    assert loaded_event == event
