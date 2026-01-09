# Issue Tracker API

FastAPI + PostgreSQL issue tracking service with optimistic concurrency, bulk updates, CSV import, and reporting.

## Requirements

- Python 3.11+
- PostgreSQL 13+

## Setup

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create a database and set `DATABASE_URL` (see `.env.example`).

```bash
copy .env.example .env
```

## Migrations

```bash
alembic upgrade head
```

## Run

```bash
uvicorn app.main:app --reload
```

## Domain Rules

- IssueStatus: `OPEN`, `IN_PROGRESS`, `RESOLVED`, `CLOSED`
- Bulk status update rules (transactional, rollback on any violation):
  - Rule A: cannot set `RESOLVED` or `CLOSED` if `assignee_id` is null
  - Rule B: cannot set `CLOSED` directly from `OPEN` (must be `IN_PROGRESS` or `RESOLVED` first)
- `resolved_at` behavior:
  - If status becomes `RESOLVED` or `CLOSED`, set `resolved_at = now()` if it was null
  - If status changes away from `RESOLVED`/`CLOSED`, clear `resolved_at = null`

## CSV Import Rules

Required columns: `title`, `description`, `status`, `assignee_email`, `labels`

- `title` must be non-empty
- `status` must be one of the enum values (if empty, defaults to `OPEN`)
- `assignee_email` must map to an existing user (otherwise row is invalid)
- `labels` are semicolon-separated, trimmed, empty tokens ignored
- Transactional import: if any row is invalid, no rows are inserted
- Error `row_number` uses the CSV line number (header = 1)

## API Examples

Create an issue:

```bash
curl -X POST http://127.0.0.1:8000/issues \
  -H "Content-Type: application/json" \
  -d '{"title":"Login bug","description":"Fails on retry","assignee_id":1}'
```

List issues:

```bash
curl "http://127.0.0.1:8000/issues?status=OPEN&assignee_id=1&label=bug&limit=10&offset=0&sort=created_at&order=desc"
```

Get issue:

```bash
curl http://127.0.0.1:8000/issues/1
```

Update issue (optimistic versioning):

```bash
curl -X PATCH http://127.0.0.1:8000/issues/1 \
  -H "Content-Type: application/json" \
  -d '{"title":"Updated","version":1}'
```

Add comment:

```bash
curl -X POST http://127.0.0.1:8000/issues/1/comments \
  -H "Content-Type: application/json" \
  -d '{"body":"Needs repro steps","author_id":1}'
```

Replace labels:

```bash
curl -X PUT http://127.0.0.1:8000/issues/1/labels \
  -H "Content-Type: application/json" \
  -d '{"labels":["bug","urgent"]}'
```

Bulk status update:

```bash
curl -X POST http://127.0.0.1:8000/issues/bulk-status \
  -H "Content-Type: application/json" \
  -d '{"issue_ids":[1,2,3],"new_status":"IN_PROGRESS"}'
```

CSV import:

```bash
curl -X POST http://127.0.0.1:8000/issues/import \
  -F "file=@issues.csv"
```

Top assignees:

```bash
curl "http://127.0.0.1:8000/reports/top-assignees?limit=10"
```

Latency report:

```bash
curl "http://127.0.0.1:8000/reports/latency"
```

Timeline:

```bash
curl http://127.0.0.1:8000/issues/1/timeline
```

## Tests

```bash
pytest
```
