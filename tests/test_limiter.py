import uuid
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.config import settings


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client


@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/")

    assert response.status_code == 200
    assert response.json() is not None


@pytest.mark.asyncio
async def test_check_returns_valid_response(client):
    client_key = f"test:{uuid.uuid4()}"

    response = await client.post(
        "/check",
        json={"client_key": client_key},
    )

    data = response.json()

    assert response.status_code == 200
    assert "allowed" in data
    assert "tokens_remaining" in data
    assert "client_key" in data
    assert data["client_key"] == client_key
    assert isinstance(data["allowed"], bool)


@pytest.mark.asyncio
async def test_admin_can_create_limit(client):
    client_key = f"test:{uuid.uuid4()}"

    response = await client.post(
        "/admin/limits",
        headers={
            "X-Admin-Key": settings.ADMIN_SECRET
        },
        json={
            "client_key": client_key,
            "max_tokens": 3,
            "refill_rate": 0.0,
            "algorithm": "token_bucket",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "updated"


@pytest.mark.asyncio
async def test_admin_rejects_invalid_key(client):
    response = await client.post(
        "/admin/limits",
        headers={
            "X-Admin-Key": "wrong"
        },
        json={
            "client_key": "test",
        },
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_rate_limit_enforced(client):
    client_key = f"hammer:{uuid.uuid4()}"

    # Create a tiny bucket
    await client.post(
        "/admin/limits",
        headers={
            "X-Admin-Key": settings.ADMIN_SECRET
        },
        json={
            "client_key": client_key,
            "max_tokens": 3,
            "refill_rate": 0.0,
            "algorithm": "token_bucket",
        },
    )

    results = []

    for _ in range(10):
        response = await client.post(
            "/check",
            json={"client_key": client_key},
        )
        results.append(response.json()["allowed"])

    allowed_count = sum(results)
    denied_count = len(results) - allowed_count

    assert allowed_count == 3
    assert denied_count == 7


@pytest.mark.asyncio
async def test_bucket_refills(client):
    import asyncio

    client_key = f"refill:{uuid.uuid4()}"

    await client.post(
        "/admin/limits",
        headers={
            "X-Admin-Key": settings.ADMIN_SECRET
        },
        json={
            "client_key": client_key,
            "max_tokens": 2,
            "refill_rate": 1.0,
            "algorithm": "token_bucket",
        },
    )

    # Consume bucket
    await client.post("/check", json={"client_key": client_key})
    await client.post("/check", json={"client_key": client_key})

    response = await client.post(
        "/check",
        json={"client_key": client_key},
    )

    assert response.json()["allowed"] is False

    # Wait for refill
    await asyncio.sleep(1.2)

    response = await client.post(
        "/check",
        json={"client_key": client_key},
    )

    assert response.json()["allowed"] is True