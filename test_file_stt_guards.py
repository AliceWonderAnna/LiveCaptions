"""Pure helpers for live vs file STT mutual exclusion."""


def can_start_live(engine, file_engine) -> bool:
    return engine is None and file_engine is None


def can_start_file(engine, file_engine) -> bool:
    return engine is None and file_engine is None


def test_mutual_exclusion_helpers():
    assert can_start_live(None, None)
    assert can_start_file(None, None)
    assert not can_start_live(object(), None)
    assert not can_start_live(None, object())
    assert not can_start_file(object(), None)
    assert not can_start_file(None, object())
