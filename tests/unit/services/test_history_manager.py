"""Tests for HistoryManager service."""

from datetime import datetime, timedelta
from pathlib import Path

from bloginator.models.history import GenerationHistoryEntry, GenerationType
from bloginator.services.history_manager import HistoryManager


def _create_entry(
    *,
    title: str,
    generation_type: GenerationType,
    classification: str = "guidance",
    audience: str = "all-disciplines",
    timestamp: datetime | None = None,
) -> GenerationHistoryEntry:
    return GenerationHistoryEntry(
        generation_type=generation_type,
        title=title,
        classification=classification,
        audience=audience,
        output_path="/tmp/out.md",
        timestamp=timestamp or datetime.now(),
    )


def test_save_and_load_entry_roundtrip(tmp_path: Path) -> None:
    manager = HistoryManager(history_dir=tmp_path)
    entry = _create_entry(title="Doc 1", generation_type=GenerationType.DRAFT)

    manager.save_entry(entry)
    loaded = manager.load_entry(entry.id)

    assert loaded is not None
    assert loaded.id == entry.id
    assert loaded.title == "Doc 1"


def test_delete_entry_removes_index_and_file(tmp_path: Path) -> None:
    manager = HistoryManager(history_dir=tmp_path)
    entry = _create_entry(title="Doc 1", generation_type=GenerationType.OUTLINE)
    manager.save_entry(entry)

    entry_file = tmp_path / f"{entry.id}.json"
    assert entry_file.exists()

    deleted = manager.delete_entry(entry.id)

    assert deleted is True
    assert not entry_file.exists()
    assert manager.load_entry(entry.id) is None


def test_query_filters_and_ordering(tmp_path: Path) -> None:
    manager = HistoryManager(history_dir=tmp_path)
    now = datetime.now()
    entries = [
        _create_entry(
            title="Outline A",
            generation_type=GenerationType.OUTLINE,
            classification="guidance",
            timestamp=now - timedelta(minutes=5),
        ),
        _create_entry(
            title="Draft B",
            generation_type=GenerationType.DRAFT,
            classification="mandate",
            timestamp=now - timedelta(minutes=1),
        ),
        _create_entry(
            title="Draft C",
            generation_type=GenerationType.DRAFT,
            classification="guidance",
            timestamp=now - timedelta(minutes=2),
        ),
    ]

    for e in entries:
        manager.save_entry(e)

    all_results = manager.query()
    assert [e.title for e in all_results] == ["Draft B", "Draft C", "Outline A"]

    draft_results = manager.query(generation_type=GenerationType.DRAFT)
    assert {e.title for e in draft_results} == {"Draft B", "Draft C"}

    guidance_results = manager.query(classification="guidance")
    assert {e.title for e in guidance_results} == {"Outline A", "Draft C"}

    limited = manager.query(limit=1)
    assert len(limited) == 1
    assert limited[0].title == "Draft B"


def test_get_recent_and_clear_all(tmp_path: Path) -> None:
    manager = HistoryManager(history_dir=tmp_path)

    for i in range(3):
        manager.save_entry(
            _create_entry(
                title=f"Doc {i}",
                generation_type=GenerationType.DRAFT,
                timestamp=datetime.now() - timedelta(minutes=i),
            )
        )

    recent = manager.get_recent(limit=2)
    assert len(recent) == 2

    cleared = manager.clear_all()
    assert cleared == 3
    assert manager.load_history().entries == []
