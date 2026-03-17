# WiDC Backend

FastAPI backend for Who is in DC.

## Run

```bash
uvicorn main:app --reload
```

## API

### 1) Presence APIs

#### `GET /get-people`
Return current online people.

Response:

```json
[
  {
    "name": "Benson",
    "entered_at": "2026-03-17T00:30:00+00:00"
  }
]
```

#### `POST /enter`
Body:

```json
{"name": "Benson"}
```

#### `POST /leave`
Body:

```json
{"name": "Benson"}
```

### 2) Leaderboard API

#### `GET /leaderboard?range=today|week|month&limit=50`
Return duration ranking in minutes for the selected window.

Response:

```json
{
  "range": "today",
  "generated_at": "2026-03-17T08:30:00+08:00",
  "items": [
    {
      "rank": 1,
      "name": "Benson",
      "duration_minutes": 125,
      "diff_from_prev_minutes": 0
    }
  ]
}
```

### 3) Heatmap API

#### `GET /heatmap?range=7d|30d&bucket=hour`
Return hourly heatmap cells with intensity value = average online people in that hour.

Response:

```json
{
  "range": "7d",
  "bucket": "hour",
  "generated_at": "2026-03-17T08:30:00+08:00",
  "cells": [
    {"date": "2026-03-16", "hour": 21, "value": 1.75}
  ],
  "summary": {
    "hottest_slot": "2026-03-16 21:00-22:00",
    "avg_online": 0.42,
    "peak_online": 3
  }
}
```

## JSON database structure (`/app/data/data.json`)

```json
{
  "schema_version": 1,
  "created_at": "2026-03-17T00:20:00+00:00",
  "updated_at": "2026-03-17T00:45:00+00:00",
  "users": {
    "benson": "Benson"
  },
  "events": [
    {
      "id": "a7dcf1ed-6a8f-4a7f-bbfd-4c7ed10de001",
      "user_id": "benson",
      "type": "enter",
      "at": "2026-03-17T00:30:00+00:00",
      "name_snapshot": "Benson"
    },
    {
      "id": "a7dcf1ed-6a8f-4a7f-bbfd-4c7ed10de002",
      "user_id": "benson",
      "type": "leave",
      "at": "2026-03-17T02:30:00+00:00",
      "name_snapshot": "Benson"
    }
  ],
  "active": {
    "benson": "a7dcf1ed-6a8f-4a7f-bbfd-4c7ed10de001"
  }
}
```

### Field notes
- `users`: stable user dictionary (`user_id -> display name`)
- `events`: append-only presence event stream
- `active`: current online index (`user_id -> latest enter event id`)
- Existing legacy format (`{"dc": [...]}`) is auto-migrated in memory and saved with schema v1 on next write.
