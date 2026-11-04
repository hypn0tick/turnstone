from unittest.mock import MagicMock, patch

import turnstone.spend as spend


def test_get_session_spend_returns_cost():
    resp = MagicMock()
    resp.json.return_value = [{"spend": 1.25, "session_id": "sess-1"}]
    with patch("turnstone.spend.httpx2.get", return_value=resp):
        assert spend.get_session_spend("sess-1") == 1.25


def test_get_user_spend_returns_cost():
    resp = MagicMock()
    resp.json.return_value = {"user_info": {"spend": 2.5}}
    with patch("turnstone.spend.httpx2.get", return_value=resp):
        assert spend.get_user_spend("user-1") == 2.5
