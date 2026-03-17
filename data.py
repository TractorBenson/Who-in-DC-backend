import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from models import EventType, PresenceEvent, PresenceStore

DATA_DIR = Path("/app/data")
DATA_FILE = DATA_DIR / "data.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _default_store() -> PresenceStore:
    now = _now_iso()
    return PresenceStore(created_at=now, updated_at=now)


def _normalize_name(name: str) -> str:
    return name.strip().lower()


def _migrate_legacy(raw: dict) -> PresenceStore:
    now = _now_iso()
    store = PresenceStore(created_at=now, updated_at=now)

    for person in raw.get("dc", []):
        name = str(person.get("name", "")).strip()
        if not name:
            continue

        user_id = _normalize_name(name)
        entered_at = str(person.get("entered_at", now))
        event_id = str(uuid4())
        store.users[user_id] = name
        store.events.append(
            PresenceEvent(
                id=event_id,
                user_id=user_id,
                type=EventType.ENTER,
                at=entered_at,
                name_snapshot=name,
            )
        )
        store.active[user_id] = event_id

    store.updated_at = now
    return store


def load_store() -> PresenceStore:
    if not DATA_FILE.exists():
        return _default_store()

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)

    if isinstance(raw, dict) and raw.get("schema_version") == 1:
        return PresenceStore.model_validate(raw)

    return _migrate_legacy(raw if isinstance(raw, dict) else {})


def save_store(store: PresenceStore) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    store.updated_at = _now_iso()

    temp_file = DATA_FILE.with_suffix(".tmp")
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(store.model_dump(), f, ensure_ascii=False, indent=2)
    temp_file.replace(DATA_FILE)
