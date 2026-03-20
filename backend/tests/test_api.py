import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock


class TestHealthCheck:
    """Tests for the health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_check(self, test_client):
        resp = await test_client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"


class TestAnalyzeEndpoint:
    """Tests for the /api/analyze endpoint."""

    @pytest.mark.asyncio
    async def test_analyze_creates_player(self, test_client):
        with patch("app.routers.analysis._run_analysis", new_callable=AsyncMock):
            resp = await test_client.post(
                "/api/analyze",
                json={"username": "testplayer", "time_control": "all", "game_count": 10},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "analyzing"
            assert data["username"] == "testplayer"

    @pytest.mark.asyncio
    async def test_analyze_empty_username(self, test_client):
        resp = await test_client.post(
            "/api/analyze",
            json={"username": "  ", "time_control": "all", "game_count": 10},
        )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_analyze_duplicate(self, test_client):
        with patch("app.routers.analysis._run_analysis", new_callable=AsyncMock):
            # First request
            resp1 = await test_client.post(
                "/api/analyze",
                json={"username": "dupetest"},
            )
            assert resp1.status_code == 200

            # Second request — should get 409 since status is "analyzing"
            resp2 = await test_client.post(
                "/api/analyze",
                json={"username": "dupetest"},
            )
            assert resp2.status_code == 409


class TestStatusEndpoint:
    """Tests for the /api/status endpoint."""

    @pytest.mark.asyncio
    async def test_status_not_found(self, test_client):
        resp = await test_client.get("/api/status/nonexistent")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_status_after_analyze(self, test_client):
        with patch("app.routers.analysis._run_analysis", new_callable=AsyncMock):
            await test_client.post(
                "/api/analyze",
                json={"username": "statustest"},
            )
            resp = await test_client.get("/api/status/statustest")
            assert resp.status_code == 200
            data = resp.json()
            assert data["username"] == "statustest"
            assert data["status"] == "analyzing"


class TestPlayersEndpoint:
    """Tests for the /api/players endpoints."""

    @pytest.mark.asyncio
    async def test_list_players_empty(self, test_client):
        resp = await test_client.get("/api/players")
        assert resp.status_code == 200
        data = resp.json()
        assert data["players"] == []

    @pytest.mark.asyncio
    async def test_list_players_after_analyze(self, test_client):
        with patch("app.routers.analysis._run_analysis", new_callable=AsyncMock):
            await test_client.post(
                "/api/analyze",
                json={"username": "listtest"},
            )
            resp = await test_client.get("/api/players")
            assert resp.status_code == 200
            players = resp.json()["players"]
            assert len(players) >= 1
            usernames = [p["username"] for p in players]
            assert "listtest" in usernames

    @pytest.mark.asyncio
    async def test_delete_player(self, test_client):
        with patch("app.routers.analysis._run_analysis", new_callable=AsyncMock):
            await test_client.post(
                "/api/analyze",
                json={"username": "deletetest"},
            )

            # Wait a moment then delete (the bg task is mocked so status stays "analyzing")
            # First manually set status to non-analyzing via a second request
            # Instead, just delete directly
            resp = await test_client.delete("/api/players/deletetest")
            assert resp.status_code == 200
            assert resp.json()["status"] == "deleted"

    @pytest.mark.asyncio
    async def test_delete_player_not_found(self, test_client):
        resp = await test_client.delete("/api/players/ghostplayer")
        assert resp.status_code == 404


class TestReportsEndpoint:
    """Tests for the /api/reports endpoint."""

    @pytest.mark.asyncio
    async def test_report_not_found(self, test_client):
        resp = await test_client.get("/api/reports/unknownplayer")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_report_not_complete(self, test_client):
        with patch("app.routers.analysis._run_analysis", new_callable=AsyncMock):
            await test_client.post(
                "/api/analyze",
                json={"username": "incomplete"},
            )
            resp = await test_client.get("/api/reports/incomplete")
            assert resp.status_code == 404


class TestChatEndpoint:
    """Tests for the /api/chat endpoints."""

    @pytest.mark.asyncio
    async def test_chat_no_player(self, test_client):
        resp = await test_client.post(
            "/api/chat",
            json={"username": "nobody", "message": "Hello"},
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_clear_chat_not_found(self, test_client):
        resp = await test_client.delete("/api/chat/nobody")
        assert resp.status_code == 404
