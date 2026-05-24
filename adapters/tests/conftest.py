"""Shared fixtures for adapter tests.

Mocks httpx.Client so no live server is needed.
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock, patch

import pytest


class FakeResponse:
    """Minimal httpx.Response stand-in."""

    def __init__(self, data: dict[str, Any], status_code: int = 200) -> None:
        self._data = data
        self.status_code = status_code
        self.text = json.dumps(data)

    def json(self) -> dict[str, Any]:
        return self._data

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            import httpx
            request = MagicMock()
            request.url = "http://test/mock"
            raise httpx.HTTPStatusError(
                f"HTTP {self.status_code}",
                request=request,
                response=self,
            )


# ── Standard mock responses for each endpoint ─────────────────────────

HEALTH_RESPONSE = {
    "status": "ok",
    "network": "mainnet",
    "node1_reachable": True,
    "node2_reachable": True,
    "relay_count": 3,
}

CREATE_RESPONSE = {
    "instrument_id": "aaaa-bbbb-cccc-dddd",
    "p2tr_address": "bc1p" + "a" * 58,
    "sealed_payload": "encrypted...",
    "fee_sats": 250,
    "fee_address": "bc1q" + "b" * 38,
}

CONFIRM_RESPONSE = {
    "status": "confirmed",
    "instrument_id": "aaaa-bbbb-cccc-dddd",
    "confirmed_block_height": 850000,
}

VERIFY_RESPONSE = {
    "address": "bc1p" + "a" * 58,
    "node1_balance": 50000,
    "node2_balance": 50000,
    "nodes_agree": True,
    "mempool_clean": True,
}

ATTESTATION_RESPONSE = {
    "instrument_id": "aaaa-bbbb-cccc-dddd",
    "attestation_type": "local",
    "code_hash": "ab" * 32,
    "ka_deleted_at": "2026-05-18T10:00:00Z",
}

STATUS_RESPONSE = {
    "instrument_id": "aaaa-bbbb-cccc-dddd",
    "status": "confirmed",
    "amount_sats": 50000,
    "p2tr_address": "bc1p" + "a" * 58,
}

BATCH_CREATE_RESPONSE = {
    "batch_id": "bbbb-1111-2222-3333",
    "instruments": [
        {"instrument_id": "i1", "p2tr_address": "bc1p" + "c" * 58},
        {"instrument_id": "i2", "p2tr_address": "bc1p" + "d" * 58},
    ],
}

BATCH_STATUS_RESPONSE = {
    "batch_id": "bbbb-1111-2222-3333",
    "instruments": [
        {"instrument_id": "i1", "status": "created"},
        {"instrument_id": "i2", "status": "created"},
    ],
}

WATCH_RESPONSE = {
    "watch_id": "wwww-1111-2222-3333",
    "status": "watching",
    "expires_at": "2026-05-18T10:10:00Z",
}

DELETE_WATCH_RESPONSE = {
    "watch_id": "wwww-1111-2222-3333",
    "status": "deleted",
}

AGENT_RESPONSE = {
    "pubkey": "aa" * 32,
    "display_name": "TestAgent",
    "capabilities": ["payment"],
    "reputation": {"instruments_created": 5, "instruments_disputed": 0},
}

UPDATE_AGENT_RESPONSE = {
    "pubkey": "aa" * 32,
    "display_name": "NewName",
    "capabilities": ["payment", "escrow"],
}

AGENT_CARD_RESPONSE = {
    "name": "TestAgent",
    "version": "0.6.2",
    "capabilities": [{"name": "payment"}],
    "kagikai": {"pubkey": "aa" * 32},
}

REPUTATION_RESPONSE = {
    "pubkey": "aa" * 32,
    "instruments_created": 10,
    "instruments_received": 5,
    "instruments_transferred": 3,
    "instruments_disputed": 0,
}

SUBMIT_RESPONSE = {
    "instrument_id": "aaaa-bbbb-cccc-dddd",
    "status": "submitted",
    "evidence": "https://example.com/proof",
}

COMPLETE_RESPONSE = {
    "instrument_id": "aaaa-bbbb-cccc-dddd",
    "status": "completed",
}

REJECT_RESPONSE = {
    "instrument_id": "aaaa-bbbb-cccc-dddd",
    "status": "rejected",
    "reason": "deliverable not matching",
}

# ── Phase 10/11/14 mock responses ─────────────────────────────────────

ESCROW_CREATE_RESPONSE = {
    "instrument_id": "eeee-1111-2222-3333",
    "p2tr_address": "bc1p" + "e" * 58,
    "amount_sats": 50000,
    "status": "created",
}

ESCROW_STATUS_RESPONSE = {
    "instrument_id": "eeee-1111-2222-3333",
    "status": "confirmed",
    "amount_sats": 50000,
}

ESCROW_RELEASE_RESPONSE = {
    "instrument_id": "eeee-1111-2222-3333",
    "status": "submitted",
    "evidence": "https://example.com/proof",
}

ESCROW_CANCEL_RESPONSE = {
    "instrument_id": "eeee-1111-2222-3333",
    "status": "rejected",
    "reason": "buyer cancelled",
}

SET_DESTINATION_RESPONSE = {
    "instrument_id": "aaaa-bbbb-cccc-dddd",
    "status": "destination_set",
}

LIST_AVAILABLE_RESPONSE = {
    "instruments": [
        {"instrument_id": "v1", "amount_sats": 10000, "status": "available"},
        {"instrument_id": "v2", "amount_sats": 20000, "status": "available"},
    ],
}

RECYCLE_RESPONSE = {
    "instrument_id": "aaaa-bbbb-cccc-dddd",
    "new_instrument_id": "rrrr-1111-2222-3333",
    "status": "created",
}

REFUND_RESPONSE = {
    "instrument_id": "aaaa-bbbb-cccc-dddd",
    "status": "refunding",
    "refund_txid": "ff" * 32,
}

FEE_ESTIMATE_RESPONSE = {
    "amount_sats": 50000,
    "fee_sats": 250,
    "fee_basis_points": 50,
    "fee_address": "bc1q" + "f" * 38,
}

DISPUTE_RESPONSE = {
    "instrument_id": "aaaa-bbbb-cccc-dddd",
    "status": "disputed",
    "bond_instrument_id": "bond-1111",
    "bond_amount_sats": 5000,
}

RESOLVE_DISPUTE_RESPONSE = {
    "instrument_id": "aaaa-bbbb-cccc-dddd",
    "status": "completed",
    "resolution": "uphold",
}

# Maps URL path fragments to mock responses
ENDPOINT_MAP = {
    "/health": HEALTH_RESPONSE,
    "/v1/instrument/create": CREATE_RESPONSE,
    "/v1/instrument/confirm": CONFIRM_RESPONSE,
    "/v1/verify": VERIFY_RESPONSE,
    "/v1/attestation/": ATTESTATION_RESPONSE,
    "/v1/instrument/": STATUS_RESPONSE,
    "/v1/batch/create": BATCH_CREATE_RESPONSE,
    "/v1/batch/": BATCH_STATUS_RESPONSE,
    "/v1/receipt/watch": WATCH_RESPONSE,
    "/v1/agent/": AGENT_RESPONSE,
    "/v1/reputation/": REPUTATION_RESPONSE,
    "/v1/instrument/submit": SUBMIT_RESPONSE,
    "/v1/instrument/complete": COMPLETE_RESPONSE,
    "/v1/instrument/reject": REJECT_RESPONSE,
    "/v1/instrument/set-destination": SET_DESTINATION_RESPONSE,
    "/v1/instrument/available": LIST_AVAILABLE_RESPONSE,
    "/v1/instrument/recycle": RECYCLE_RESPONSE,
    "/v1/instrument/refund": REFUND_RESPONSE,
    "/v1/fee-estimate": FEE_ESTIMATE_RESPONSE,
    "/v1/instrument/dispute": DISPUTE_RESPONSE,
    "/v1/instrument/resolve": RESOLVE_DISPUTE_RESPONSE,
}


def _make_mock_client(response_data: dict[str, Any]) -> MagicMock:
    """Build a mock httpx.Client context manager returning the given data."""
    mock_client = MagicMock()
    mock_response = FakeResponse(response_data)
    mock_client.get.return_value = mock_response
    mock_client.post.return_value = mock_response
    mock_client.put.return_value = mock_response
    mock_client.delete.return_value = mock_response
    return mock_client


@pytest.fixture
def mock_httpx_health():
    """Patch httpx.Client to return health response."""
    client = _make_mock_client(HEALTH_RESPONSE)
    with patch("httpx.Client") as mock_cls:
        mock_cls.return_value.__enter__ = MagicMock(return_value=client)
        mock_cls.return_value.__exit__ = MagicMock(return_value=False)
        yield client


@pytest.fixture
def mock_httpx_factory():
    """Factory fixture: call with response data to get a patched httpx.Client."""
    def _factory(data: dict[str, Any]):
        client = _make_mock_client(data)
        patcher = patch("httpx.Client")
        mock_cls = patcher.start()
        mock_cls.return_value.__enter__ = MagicMock(return_value=client)
        mock_cls.return_value.__exit__ = MagicMock(return_value=False)
        return client, patcher
    return _factory
