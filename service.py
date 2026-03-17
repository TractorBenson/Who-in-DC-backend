from collections import defaultdict
from datetime import datetime, time, timedelta
from math import ceil
from uuid import uuid4

from data import load_store, save_store
from models import EventType, PresenceEvent

LOCAL_TZ = datetime.now().astimezone().tzinfo


def _parse_iso(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def _to_local(dt: datetime) -> datetime:
    return dt.astimezone(LOCAL_TZ)


def _window_for_leaderboard(range_name: str, now_local: datetime) -> tuple[datetime, datetime]:
    if range_name == "today":
        start = datetime.combine(now_local.date(), time.min, tzinfo=LOCAL_TZ)
    elif range_name == "week":
        start_day = now_local.date() - timedelta(days=now_local.weekday())
        start = datetime.combine(start_day, time.min, tzinfo=LOCAL_TZ)
    elif range_name == "month":
        start = datetime.combine(now_local.date().replace(day=1), time.min, tzinfo=LOCAL_TZ)
    else:
        raise ValueError("range must be one of: today, week, month")
    return start, now_local


def _window_for_heatmap(range_name: str, now_local: datetime) -> tuple[datetime, datetime]:
    if range_name == "7d":
        days = 7
    elif range_name == "30d":
        days = 30
    else:
        raise ValueError("range must be one of: 7d, 30d")

    end = now_local
    start = datetime.combine((end - timedelta(days=days - 1)).date(), time.min, tzinfo=LOCAL_TZ)
    return start, end


def _build_intervals(events: list[PresenceEvent], window_end_local: datetime) -> list[tuple[str, datetime, datetime]]:
    sorted_events = sorted(events, key=lambda e: _parse_iso(e.at))
    opened: dict[str, datetime] = {}
    intervals: list[tuple[str, datetime, datetime]] = []

    for event in sorted_events:
        event_time_local = _to_local(_parse_iso(event.at))
        if event.type == EventType.ENTER:
            opened[event.user_id] = event_time_local
        elif event.user_id in opened:
            start_local = opened.pop(event.user_id)
            if event_time_local > start_local:
                intervals.append((event.user_id, start_local, event_time_local))

    for user_id, start_local in opened.items():
        if window_end_local > start_local:
            intervals.append((user_id, start_local, window_end_local))

    return intervals


def _overlap_seconds(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> float:
    start = max(a_start, b_start)
    end = min(a_end, b_end)
    if end <= start:
        return 0.0
    return (end - start).total_seconds()


def _get_or_create_user_id(users: dict[str, str], name: str) -> str:
    user_id = name.strip().lower()
    if user_id not in users:
        users[user_id] = name
    return user_id


def get_people() -> list[dict]:
    store = load_store()
    enter_time_by_user = {event.id: event.at for event in store.events if event.type == EventType.ENTER}

    people = []
    for user_id, enter_event_id in store.active.items():
        name = store.users.get(user_id, user_id)
        entered_at = enter_time_by_user.get(enter_event_id)
        if entered_at:
            people.append({"name": name, "entered_at": entered_at})

    people.sort(key=lambda item: item["entered_at"])
    return people


def enter_dc(name: str) -> None:
    store = load_store()
    user_id = _get_or_create_user_id(store.users, name)

    if user_id in store.active:
        return

    event = PresenceEvent(
        id=str(uuid4()),
        user_id=user_id,
        type=EventType.ENTER,
        at=datetime.now().astimezone().isoformat(),
        name_snapshot=name,
    )
    store.events.append(event)
    store.active[user_id] = event.id
    save_store(store)


def leave_dc(name: str) -> None:
    store = load_store()
    user_id = name.strip().lower()
    if user_id not in store.active:
        return

    event = PresenceEvent(
        id=str(uuid4()),
        user_id=user_id,
        type=EventType.LEAVE,
        at=datetime.now().astimezone().isoformat(),
        name_snapshot=store.users.get(user_id, name),
    )
    store.events.append(event)
    store.active.pop(user_id, None)
    save_store(store)


def get_leaderboard(range_name: str = "today", limit: int = 50) -> dict:
    store = load_store()
    now_local = datetime.now().astimezone()
    window_start, window_end = _window_for_leaderboard(range_name, now_local)

    durations = defaultdict(float)
    intervals = _build_intervals(store.events, window_end)

    for user_id, start_local, end_local in intervals:
        durations[user_id] += _overlap_seconds(start_local, end_local, window_start, window_end)

    ranked = sorted(
        ((user_id, secs) for user_id, secs in durations.items() if secs > 0),
        key=lambda item: (-item[1], store.users.get(item[0], item[0])),
    )

    rows = []
    prev_seconds = None
    rank = 0
    for index, (user_id, seconds) in enumerate(ranked[: max(limit, 1)], start=1):
        if prev_seconds is None or seconds < prev_seconds:
            rank = index
        prev_seconds = seconds

        diff = 0 if index == 1 else max(0, int((ranked[index - 2][1] - seconds) // 60))
        rows.append(
            {
                "rank": rank,
                "name": store.users.get(user_id, user_id),
                "duration_minutes": int(seconds // 60),
                "diff_from_prev_minutes": diff,
            }
        )

    return {"range": range_name, "generated_at": now_local.isoformat(), "items": rows}


def get_heatmap(range_name: str = "7d", bucket: str = "hour") -> dict:
    if bucket != "hour":
        raise ValueError("bucket must be hour")

    store = load_store()
    now_local = datetime.now().astimezone()
    window_start, window_end = _window_for_heatmap(range_name, now_local)

    intervals = _build_intervals(store.events, window_end)

    buckets: dict[tuple[str, int], float] = defaultdict(float)
    timeline_points: list[tuple[datetime, int]] = []

    for _user_id, start_local, end_local in intervals:
        clipped_start = max(start_local, window_start)
        clipped_end = min(end_local, window_end)
        if clipped_end <= clipped_start:
            continue

        timeline_points.append((clipped_start, 1))
        timeline_points.append((clipped_end, -1))

        cursor = clipped_start.replace(minute=0, second=0, microsecond=0)
        while cursor < clipped_end:
            next_hour = cursor + timedelta(hours=1)
            seconds = _overlap_seconds(clipped_start, clipped_end, cursor, next_hour)
            if seconds > 0:
                key = (cursor.date().isoformat(), cursor.hour)
                buckets[key] += seconds
            cursor = next_hour

    cells = []
    hottest_slot = None
    hottest_value = -1.0

    day = window_start.date()
    while day <= window_end.date():
        for hour in range(24):
            key = (day.isoformat(), hour)
            value = round(buckets.get(key, 0.0) / 3600.0, 3)
            cells.append({"date": key[0], "hour": key[1], "value": value})
            if value > hottest_value:
                hottest_value = value
                hottest_slot = f"{key[0]} {hour:02d}:00-{(hour + 1) % 24:02d}:00"
        day += timedelta(days=1)

    active = 0
    peak_online = 0
    for _time, delta in sorted(timeline_points, key=lambda item: (item[0], item[1])):
        active += delta
        peak_online = max(peak_online, active)

    summary = {
        "hottest_slot": hottest_slot,
        "avg_online": round(sum(cell["value"] for cell in cells) / len(cells), 3) if cells else 0.0,
        "peak_online": max(peak_online, ceil(hottest_value)) if hottest_value > 0 else 0,
    }

    return {
        "range": range_name,
        "bucket": bucket,
        "generated_at": now_local.isoformat(),
        "cells": cells,
        "summary": summary,
    }
