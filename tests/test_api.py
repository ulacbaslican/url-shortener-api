import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from database import Base, get_db
from main import app


@pytest.fixture(scope="session", autouse=True)
def override_database_dependency():
	engine = create_engine(
		"sqlite://",
		connect_args={"check_same_thread": False},
		poolclass=StaticPool,
	)
	TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
	Base.metadata.create_all(bind=engine)

	def override_get_db():
		db = TestingSessionLocal()
		try:
			yield db
		finally:
			db.close()

	app.state.queue = None
	app.state.redis = None
	app.dependency_overrides[get_db] = override_get_db
	yield
	app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_shorten_url():
	async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
		response = await client.post(
			"/shorten",
			json={"original_url": "https://example.com"},
		)

	assert response.status_code == 200
	assert "short_code" in response.json()


@pytest.mark.asyncio
async def test_shorten_invalid_url():
	async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
		response = await client.post(
			"/shorten",
			json={"original_url": "not-a-url"},
		)

	assert response.status_code == 422


@pytest.mark.asyncio
async def test_redirect():
	original_url = "https://example.com/redirect-target"
	async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
		create_response = await client.post(
			"/shorten",
			json={"original_url": original_url},
		)
		short_code = create_response.json()["short_code"]
		redirect_response = await client.get(f"/{short_code}")

	assert redirect_response.status_code == 302
	assert original_url in redirect_response.headers["location"]


@pytest.mark.asyncio
async def test_stats():
	original_url = "https://example.com/stats-target"
	async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
		create_response = await client.post(
			"/shorten",
			json={"original_url": original_url},
		)
		short_code = create_response.json()["short_code"]
		await client.get(f"/{short_code}")
		stats_response = await client.get(f"/stats/{short_code}")

	assert stats_response.status_code == 200
	assert stats_response.json()["click_count"] == 1


@pytest.mark.asyncio
async def test_custom_code():
	async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
		response = await client.post(
			"/shorten",
			json={"original_url": "https://example.com/custom", "custom_code": "mytest"},
		)

	assert response.status_code == 200
	assert response.json()["short_code"] == "mytest"


@pytest.mark.asyncio
async def test_duplicate_custom_code():
	async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
		first_response = await client.post(
			"/shorten",
			json={"original_url": "https://example.com/first", "custom_code": "duplicate"},
		)
		second_response = await client.post(
			"/shorten",
			json={"original_url": "https://example.com/second", "custom_code": "duplicate"},
		)

	assert first_response.status_code == 200
	assert second_response.status_code == 409


@pytest.mark.asyncio
async def test_delete():
	async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
		create_response = await client.post(
			"/shorten",
			json={"original_url": "https://example.com/delete-target"},
		)
		short_code = create_response.json()["short_code"]
		delete_response = await client.delete(f"/urls/{short_code}")

	assert delete_response.status_code == 200
