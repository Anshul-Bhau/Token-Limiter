# Token Bucket Rate Limiter Service

A standalone rate-limiting API that returns ALLOW or DENY for any client key. Built with FastAPI, Redis, and MySQL.

## How it works

Other services call `POST /check` before serving their own requests. This service looks up the client's token bucket in Redis, atomically deducts a token via a Lua script, and returns `allowed: true` or `allowed: false`. The calling service decides what to do with that response.

Token buckets refill automatically over time — a client with `max_tokens=10` and `refill_rate=2.0` gets 2 tokens back every second, up to a ceiling of 10. Burst traffic drains the bucket fast; sustained traffic stays within the refill rate.

Client config (limits, algorithm) lives in MySQL and is cached in Redis for 60 seconds. All live bucket state lives purely in Redis. The Lua script ensures the read-modify-write is atomic — no double-spending tokens under concurrent load.

## Stack

- **FastAPI** — API framework
- **Redis** — bucket state storage (atomic Lua scripts)
- **MySQL** — per-client config storage
- **Alembic** — migrations
- **Locust** — load testing

## Setup

```bash
# clone and enter
git clone https://github.com/YOUR_USERNAME/rate-limiter.git
cd rate-limiter

# create and activate venv
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# install dependencies
pip install -r requirements.txt

# copy env and fill in values
cp .env.example .env

# run migrations
alembic upgrade head

# start server
uvicorn app.main:app --reload --port 8000
```

## Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/check` | Check if a client key is allowed |
| `POST` | `/admin/limits` | Set per-client rate limits |
| `GET` | `/stats` | Live request stats per client |
| `GET` | `/` | Health check |

### POST /check
```json
// request
{ "client_key": "user:abc123" }

// response
{ "allowed": true, "tokens_remaining": 4.0, "client_key": "user:abc123" }
```

### POST /admin/limits
```json
// header: X-Admin-Key: <your secret>

{
  "client_key": "user:abc123",
  "max_tokens": 20,
  "refill_rate": 5.0,
  "algorithm": "token_bucket"
}
```

## Algorithms

- **Token bucket** (default) — continuous refill, allows bursting
- **Sliding window** — rolling time window, switchable per client via `/admin/limits`

## Load Test

```bash
locust -f locustfile.py --headless --users 500 --spawn-rate 50 --run-time 30s --host http://localhost:8000
```

Results: **~1,000 req/s, 0% failure rate** at 500 concurrent users.

## Environment Variables

| Variable | Description |
|---|---|
| `REDIS_URL` | Redis connection string |
| `MYSQL_URL` | MySQL connection string |
| `ADMIN_SECRET` | Secret key for admin endpoint |
| `DEFAULT_MAX_TOKENS` | Default burst limit |
| `DEFAULT_REFILL_RATE` | Default tokens per second |

## Project Structure

```
app/
├── main.py           # FastAPI app + lifespan
├── config.py         # Settings from .env
├── database.py       # Async SQLAlchemy
├── models.py         # MySQL ORM models
├── schemas.py        # Pydantic models
├── redis_client.py   # Redis connection + Lua loader
├── limiter.py        # Core rate limit logic
├── routers/
│   ├── check.py      # POST /check
│   └── admin.py      # POST /admin/limits
└── dashboard/
    └── routes.py     # GET /stats
scripts/lua/
├── token_bucket.lua
└── sliding_window.lua
```
