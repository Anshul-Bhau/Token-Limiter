import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_check_returns_allowed():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/check", json={"client_key": "test:user1"})
    assert r.status_code == 200
    assert "allowed" in r.json()


@pytest.mark.asyncio
async def test_rate_limit_enforced():
    """Hammer one client key — eventually must get denied."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        results = []
        for _ in range(20):
            r = await client.post("/check", json={"client_key": "test:hammer"})
            results.append(r.json()["allowed"])
    assert False in results  # at least one denial