"""Tests for kagikai-langchain: all 29 tools with mocked HTTP."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

# We need to add the adapter paths so imports work without pip install
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "langchain"))

from kagikai_langchain._http import KagikaiAPI
from kagikai_langchain.tools import (
    KagikaiHealth,
    KagikaiCreateInstrument,
    KagikaiConfirmInstrument,
    KagikaiVerifyAddress,
    KagikaiGetAttestation,
    KagikaiGetStatus,
    KagikaiCreateBatch,
    KagikaiGetBatchStatus,
    KagikaiWatchReceipt,
    KagikaiDeleteWatch,
    KagikaiGetAgent,
    KagikaiUpdateAgent,
    KagikaiGetAgentCard,
    KagikaiGetReputation,
    KagikaiSubmitInstrument,
    KagikaiCompleteInstrument,
    KagikaiRejectInstrument,
    KagikaiVerifyTdxQuote,
    KagikaiEscrowCreate,
    KagikaiEscrowStatus,
    KagikaiEscrowRelease,
    KagikaiEscrowCancel,
    KagikaiSetDestination,
    KagikaiListAvailable,
    KagikaiRecycleInstrument,
    KagikaiRefundInstrument,
    KagikaiFeeEstimate,
    KagikaiDisputeInstrument,
    KagikaiResolveDispute,
)
from kagikai_langchain.toolkit import KagikaiToolkit

from conftest import (
    FakeResponse,
    HEALTH_RESPONSE,
    CREATE_RESPONSE,
    CONFIRM_RESPONSE,
    VERIFY_RESPONSE,
    ATTESTATION_RESPONSE,
    STATUS_RESPONSE,
    BATCH_CREATE_RESPONSE,
    BATCH_STATUS_RESPONSE,
    WATCH_RESPONSE,
    DELETE_WATCH_RESPONSE,
    AGENT_RESPONSE,
    UPDATE_AGENT_RESPONSE,
    AGENT_CARD_RESPONSE,
    REPUTATION_RESPONSE,
    SUBMIT_RESPONSE,
    COMPLETE_RESPONSE,
    REJECT_RESPONSE,
    ESCROW_STATUS_RESPONSE,
    ESCROW_RELEASE_RESPONSE,
    ESCROW_CANCEL_RESPONSE,
    SET_DESTINATION_RESPONSE,
    LIST_AVAILABLE_RESPONSE,
    RECYCLE_RESPONSE,
    REFUND_RESPONSE,
    FEE_ESTIMATE_RESPONSE,
    DISPUTE_RESPONSE,
    RESOLVE_DISPUTE_RESPONSE,
)


# ── Helper ─────────────────────────────────────────────────────────────


def _mock_api(response_data: dict) -> tuple[KagikaiAPI, MagicMock]:
    """Create KagikaiAPI with mocked httpx.Client returning response_data."""
    api = KagikaiAPI(base_url="http://test-server", api_key="test-key")
    mock_client = MagicMock()
    mock_response = FakeResponse(response_data)
    mock_client.get.return_value = mock_response
    mock_client.post.return_value = mock_response
    mock_client.put.return_value = mock_response
    mock_client.delete.return_value = mock_response
    return api, mock_client


def _patch_and_run(tool_cls, response_data: dict, run_kwargs: dict | None = None, **tool_kwargs):
    """Patch httpx.Client, instantiate tool, call _run, return parsed result."""
    api, mock_client = _mock_api(response_data)

    with patch("httpx.Client") as mock_cls:
        mock_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_cls.return_value.__exit__ = MagicMock(return_value=False)

        tool = tool_cls(api=api, **tool_kwargs)
        result_str = tool._run(**(run_kwargs or {}))
        result = json.loads(result_str)
        return result, mock_client


# ── Tests ──────────────────────────────────────────────────────────────


class TestKagikaiAPI:
    """Test the HTTP helper directly."""

    def test_constructor_from_args(self):
        api = KagikaiAPI(base_url="http://x", api_key="k")
        assert api.base_url == "http://x"
        assert api.api_key == "k"

    def test_constructor_strips_trailing_slash(self):
        api = KagikaiAPI(base_url="http://x/", api_key="k")
        assert api.base_url == "http://x"

    def test_constructor_from_env(self, monkeypatch):
        monkeypatch.setenv("KAGIKAI_BASE_URL", "http://env-url")
        monkeypatch.setenv("KAGIKAI_API_KEY", "env-key")
        api = KagikaiAPI()
        assert api.base_url == "http://env-url"
        assert api.api_key == "env-key"

    def test_auth_headers(self):
        api = KagikaiAPI(base_url="http://x", api_key="secret")
        h = api._headers(auth=True)
        assert h["Authorization"] == "Bearer secret"

    def test_no_auth_headers(self):
        api = KagikaiAPI(base_url="http://x", api_key="secret")
        h = api._headers(auth=False)
        assert "Authorization" not in h


class TestHealth:
    def test_health_returns_status(self):
        result, mock = _patch_and_run(KagikaiHealth, HEALTH_RESPONSE)
        assert result["status"] == "ok"
        assert result["network"] == "mainnet"
        mock.get.assert_called_once()

    def test_health_no_auth(self):
        # Verify the GET call does not include auth
        api, mock_client = _mock_api(HEALTH_RESPONSE)
        with patch("httpx.Client") as mock_cls:
            mock_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
            mock_cls.return_value.__exit__ = MagicMock(return_value=False)
            tool = KagikaiHealth(api=api)
            tool._run()
        # The call was made via api.get(..., auth=False), check no Authorization header
        call_args = mock_client.get.call_args
        headers = call_args.kwargs.get("headers", {})
        assert "Authorization" not in headers


class TestCreateInstrument:
    def test_create_returns_instrument_id(self):
        result, mock = _patch_and_run(
            KagikaiCreateInstrument,
            CREATE_RESPONSE,
            run_kwargs={
                "amount_sats": 50000,
                "agent_x25519_pubkey": "aa" * 32,
            },
        )
        assert result["instrument_id"] == "aaaa-bbbb-cccc-dddd"
        mock.post.assert_called_once()

    def test_create_with_optional_fields(self):
        result, mock = _patch_and_run(
            KagikaiCreateInstrument,
            CREATE_RESPONSE,
            run_kwargs={
                "amount_sats": 50000,
                "agent_x25519_pubkey": "aa" * 32,
                "job_id": "job-123",
                "locktime_blocks": 144,
            },
        )
        body = mock.post.call_args.kwargs["json"]
        assert body["job_id"] == "job-123"
        assert body["locktime_blocks"] == 144

    def test_create_without_locktime(self):
        result, mock = _patch_and_run(
            KagikaiCreateInstrument,
            CREATE_RESPONSE,
            run_kwargs={
                "amount_sats": 50000,
                "agent_x25519_pubkey": "aa" * 32,
            },
        )
        body = mock.post.call_args.kwargs["json"]
        assert "locktime_blocks" not in body


class TestConfirmInstrument:
    def test_confirm_calls_correct_endpoint(self):
        result, mock = _patch_and_run(
            KagikaiConfirmInstrument,
            CONFIRM_RESPONSE,
            run_kwargs={
                "instrument_id": "aaaa-bbbb-cccc-dddd",
                "txid": "ff" * 32,
            },
        )
        assert result["status"] == "confirmed"
        url = mock.post.call_args.args[0]
        assert "/v1/instrument/confirm" in url


class TestVerifyAddress:
    def test_verify_address(self):
        result, mock = _patch_and_run(
            KagikaiVerifyAddress,
            VERIFY_RESPONSE,
            run_kwargs={
                "address": "bc1p" + "a" * 58,
                "expected_sats": 50000,
            },
        )
        assert result["nodes_agree"] is True


class TestGetAttestation:
    def test_attestation_no_auth(self):
        api, mock_client = _mock_api(ATTESTATION_RESPONSE)
        with patch("httpx.Client") as mock_cls:
            mock_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
            mock_cls.return_value.__exit__ = MagicMock(return_value=False)
            tool = KagikaiGetAttestation(api=api)
            result_str = tool._run(instrument_id="aaaa-bbbb-cccc-dddd")
        result = json.loads(result_str)
        assert result["attestation_type"] == "local"
        headers = mock_client.get.call_args.kwargs.get("headers", {})
        assert "Authorization" not in headers


class TestGetStatus:
    def test_get_status(self):
        result, mock = _patch_and_run(
            KagikaiGetStatus,
            STATUS_RESPONSE,
            run_kwargs={"instrument_id": "aaaa-bbbb-cccc-dddd"},
        )
        assert result["status"] == "confirmed"
        url = mock.get.call_args.args[0]
        assert "aaaa-bbbb-cccc-dddd" in url


class TestBatchCreate:
    def test_batch_create(self):
        result, mock = _patch_and_run(
            KagikaiCreateBatch,
            BATCH_CREATE_RESPONSE,
            run_kwargs={
                "instruments": [
                    {"amount_sats": 10000},
                    {"amount_sats": 20000, "label": "milestone-1"},
                ],
                "agent_x25519_pubkey": "aa" * 32,
            },
        )
        assert result["batch_id"] == "bbbb-1111-2222-3333"
        assert len(result["instruments"]) == 2


class TestBatchStatus:
    def test_batch_status(self):
        result, mock = _patch_and_run(
            KagikaiGetBatchStatus,
            BATCH_STATUS_RESPONSE,
            run_kwargs={"batch_id": "bbbb-1111-2222-3333"},
        )
        assert len(result["instruments"]) == 2


class TestWatchReceipt:
    def test_watch_receipt(self):
        result, mock = _patch_and_run(
            KagikaiWatchReceipt,
            WATCH_RESPONSE,
            run_kwargs={
                "instrument_id": "aaaa-bbbb-cccc-dddd",
                "nonce_hex": "cc" * 32,
                "kb_pubkey_hex": "dd" * 32,
                "webhook_url": "https://example.com/hook",
            },
        )
        assert result["watch_id"] == "wwww-1111-2222-3333"


class TestDeleteWatch:
    def test_delete_watch(self):
        result, mock = _patch_and_run(
            KagikaiDeleteWatch,
            DELETE_WATCH_RESPONSE,
            run_kwargs={"watch_id": "wwww-1111-2222-3333"},
        )
        assert result["status"] == "deleted"
        mock.delete.assert_called_once()


class TestGetAgent:
    def test_get_agent_no_auth(self):
        api, mock_client = _mock_api(AGENT_RESPONSE)
        with patch("httpx.Client") as mock_cls:
            mock_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
            mock_cls.return_value.__exit__ = MagicMock(return_value=False)
            tool = KagikaiGetAgent(api=api)
            result_str = tool._run(pubkey_hex="aa" * 32)
        result = json.loads(result_str)
        assert result["display_name"] == "TestAgent"
        headers = mock_client.get.call_args.kwargs.get("headers", {})
        assert "Authorization" not in headers


class TestUpdateAgent:
    def test_update_agent(self):
        result, mock = _patch_and_run(
            KagikaiUpdateAgent,
            UPDATE_AGENT_RESPONSE,
            run_kwargs={
                "pubkey_hex": "aa" * 32,
                "display_name": "NewName",
                "capabilities": ["payment", "escrow"],
            },
        )
        assert result["display_name"] == "NewName"
        mock.put.assert_called_once()

    def test_update_agent_partial(self):
        result, mock = _patch_and_run(
            KagikaiUpdateAgent,
            UPDATE_AGENT_RESPONSE,
            run_kwargs={
                "pubkey_hex": "aa" * 32,
                "display_name": "NewName",
            },
        )
        body = mock.put.call_args.kwargs["json"]
        assert "display_name" in body
        assert "capabilities" not in body
        assert "url" not in body


class TestGetAgentCard:
    def test_agent_card(self):
        result, mock = _patch_and_run(
            KagikaiGetAgentCard,
            AGENT_CARD_RESPONSE,
            run_kwargs={"pubkey_hex": "aa" * 32},
        )
        assert result["name"] == "TestAgent"
        url = mock.get.call_args.args[0]
        assert "/agent.json" in url


class TestGetReputation:
    def test_reputation(self):
        result, mock = _patch_and_run(
            KagikaiGetReputation,
            REPUTATION_RESPONSE,
            run_kwargs={"pubkey_hex": "aa" * 32},
        )
        assert result["instruments_created"] == 10
        assert result["instruments_disputed"] == 0


class TestSubmitInstrument:
    def test_submit(self):
        result, mock = _patch_and_run(
            KagikaiSubmitInstrument,
            SUBMIT_RESPONSE,
            run_kwargs={
                "instrument_id": "aaaa-bbbb-cccc-dddd",
                "evidence": "https://example.com/proof",
            },
        )
        assert result["status"] == "submitted"


class TestCompleteInstrument:
    def test_complete(self):
        result, mock = _patch_and_run(
            KagikaiCompleteInstrument,
            COMPLETE_RESPONSE,
            run_kwargs={"instrument_id": "aaaa-bbbb-cccc-dddd"},
        )
        assert result["status"] == "completed"


class TestRejectInstrument:
    def test_reject_with_reason(self):
        result, mock = _patch_and_run(
            KagikaiRejectInstrument,
            REJECT_RESPONSE,
            run_kwargs={
                "instrument_id": "aaaa-bbbb-cccc-dddd",
                "reason": "deliverable not matching",
            },
        )
        assert result["status"] == "rejected"
        body = mock.post.call_args.kwargs["json"]
        assert body["reason"] == "deliverable not matching"

    def test_reject_without_reason(self):
        result, mock = _patch_and_run(
            KagikaiRejectInstrument,
            REJECT_RESPONSE,
            run_kwargs={"instrument_id": "aaaa-bbbb-cccc-dddd"},
        )
        body = mock.post.call_args.kwargs["json"]
        assert "reason" not in body


class TestVerifyTdxQuote:
    def test_tdx_no_sdk_returns_error(self):
        """When kagikai SDK not installed, tool returns attestation + error."""
        api, mock_client = _mock_api(ATTESTATION_RESPONSE)
        with patch("httpx.Client") as mock_cls:
            mock_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
            mock_cls.return_value.__exit__ = MagicMock(return_value=False)
            tool = KagikaiVerifyTdxQuote(api=api)
            # Patch the import to fail
            with patch.dict("sys.modules", {"kagikai": None, "kagikai.tdx_verify": None}):
                result_str = tool._run(instrument_id="aaaa-bbbb-cccc-dddd")
        result = json.loads(result_str)
        assert "error" in result
        assert "kagikai SDK" in result["error"]


class TestToolkit:
    def test_toolkit_returns_29_tools(self):
        toolkit = KagikaiToolkit(base_url="http://test", api_key="key")
        tools = toolkit.get_tools()
        assert len(tools) == 29

    def test_toolkit_tools_share_api(self):
        toolkit = KagikaiToolkit(base_url="http://test", api_key="key")
        tools = toolkit.get_tools()
        apis = {id(t.api) for t in tools}
        assert len(apis) == 1, "All tools should share the same KagikaiAPI instance"

    def test_toolkit_tool_names_unique(self):
        toolkit = KagikaiToolkit(base_url="http://test", api_key="key")
        tools = toolkit.get_tools()
        names = [t.name for t in tools]
        assert len(names) == len(set(names)), "Tool names must be unique"

    def test_toolkit_env_fallback(self, monkeypatch):
        monkeypatch.setenv("KAGIKAI_BASE_URL", "http://env")
        monkeypatch.setenv("KAGIKAI_API_KEY", "env-key")
        toolkit = KagikaiToolkit()
        tools = toolkit.get_tools()
        assert tools[0].api.base_url == "http://env"
        assert tools[0].api.api_key == "env-key"


class TestHTTPErrors:
    def test_http_error_propagates(self):
        """httpx errors should propagate from tool _run."""
        import httpx
        api = KagikaiAPI(base_url="http://test", api_key="key")
        mock_client = MagicMock()
        err_response = FakeResponse({"error": "not found"}, status_code=404)
        mock_client.get.return_value = err_response

        with patch("httpx.Client") as mock_cls:
            mock_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
            mock_cls.return_value.__exit__ = MagicMock(return_value=False)
            tool = KagikaiHealth(api=api)
            with pytest.raises(httpx.HTTPStatusError):
                tool._run()


# ── Phase 10/11/14 tool tests ─────────────────────────────────────────


class TestEscrowCreate:
    def test_escrow_create(self):
        # EscrowCreate makes 2 POST calls (create + set-destination)
        # and returns a composite response with escrow_id
        result, mock = _patch_and_run(
            KagikaiEscrowCreate,
            CREATE_RESPONSE,
            run_kwargs={
                "amount_sats": 50000,
                "payee_address": "bc1p" + "e" * 58,
            },
        )
        assert result["escrow_id"] == "aaaa-bbbb-cccc-dddd"
        assert result["status"] == "watching_for_funding"
        assert mock.post.call_count == 2  # create + set-destination

    def test_escrow_create_with_evaluator(self):
        result, mock = _patch_and_run(
            KagikaiEscrowCreate,
            CREATE_RESPONSE,
            run_kwargs={
                "amount_sats": 50000,
                "payee_address": "bc1p" + "e" * 58,
                "evaluator_type": "optimistic",
                "description": "test escrow",
            },
        )
        # First call is to /v1/instrument/create
        first_call_body = mock.post.call_args_list[0].kwargs["json"]
        assert first_call_body["evaluator_type"] == "optimistic"


class TestEscrowStatus:
    def test_escrow_status(self):
        result, mock = _patch_and_run(
            KagikaiEscrowStatus,
            ESCROW_STATUS_RESPONSE,
            run_kwargs={"instrument_id": "eeee-1111-2222-3333"},
        )
        assert result["status"] == "confirmed"
        url = mock.get.call_args.args[0]
        assert "eeee-1111-2222-3333" in url


class TestEscrowRelease:
    def test_escrow_release(self):
        result, mock = _patch_and_run(
            KagikaiEscrowRelease,
            ESCROW_RELEASE_RESPONSE,
            run_kwargs={
                "instrument_id": "eeee-1111-2222-3333",
                "evidence": "https://example.com/proof",
            },
        )
        assert result["status"] == "submitted"


class TestEscrowCancel:
    def test_escrow_cancel(self):
        result, mock = _patch_and_run(
            KagikaiEscrowCancel,
            ESCROW_CANCEL_RESPONSE,
            run_kwargs={
                "instrument_id": "eeee-1111-2222-3333",
                "reason": "buyer cancelled",
            },
        )
        assert result["status"] == "rejected"

    def test_escrow_cancel_no_reason(self):
        result, mock = _patch_and_run(
            KagikaiEscrowCancel,
            ESCROW_CANCEL_RESPONSE,
            run_kwargs={"instrument_id": "eeee-1111-2222-3333"},
        )
        body = mock.post.call_args.kwargs["json"]
        assert "reason" not in body


class TestSetDestination:
    def test_set_destination(self):
        result, mock = _patch_and_run(
            KagikaiSetDestination,
            SET_DESTINATION_RESPONSE,
            run_kwargs={
                "instrument_id": "aaaa-bbbb-cccc-dddd",
                "destination_address": "bc1p" + "f" * 58,
            },
        )
        assert "destination_set" in result["status"] or "instrument_id" in result
        mock.post.assert_called_once()


class TestListAvailable:
    def test_list_available(self):
        result, mock = _patch_and_run(
            KagikaiListAvailable,
            LIST_AVAILABLE_RESPONSE,
        )
        assert len(result["instruments"]) == 2
        mock.get.assert_called_once()


class TestRecycleInstrument:
    def test_recycle(self):
        result, mock = _patch_and_run(
            KagikaiRecycleInstrument,
            RECYCLE_RESPONSE,
            run_kwargs={
                "instrument_id": "aaaa-bbbb-cccc-dddd",
                "timeout_blocks": 144,
                "evaluator_type": "optimistic",
            },
        )
        assert result["new_instrument_id"] == "rrrr-1111-2222-3333"
        mock.post.assert_called_once()


class TestRefundInstrument:
    def test_refund(self):
        result, mock = _patch_and_run(
            KagikaiRefundInstrument,
            REFUND_RESPONSE,
            run_kwargs={"instrument_id": "aaaa-bbbb-cccc-dddd"},
        )
        assert result["status"] == "refunding"
        mock.post.assert_called_once()


class TestFeeEstimate:
    def test_fee_estimate(self):
        # FeeEstimate fetches /admin/fee-config then computes locally
        result, mock = _patch_and_run(
            KagikaiFeeEstimate,
            FEE_ESTIMATE_RESPONSE,
            run_kwargs={"amount_sats": 50000},
        )
        assert result["amount_sats"] == 50000
        assert result["platform_fee_sats"] == 250  # (50000 * 50) / 10000
        assert "net_to_recipient_sats" in result


class TestDisputeInstrument:
    def test_dispute(self):
        result, mock = _patch_and_run(
            KagikaiDisputeInstrument,
            DISPUTE_RESPONSE,
            run_kwargs={
                "instrument_id": "aaaa-bbbb-cccc-dddd",
                "reason": "seller did not deliver",
            },
        )
        assert result["status"] == "disputed"
        body = mock.post.call_args.kwargs["json"]
        assert body["reason"] == "seller did not deliver"


class TestResolveDispute:
    def test_resolve_uphold(self):
        result, mock = _patch_and_run(
            KagikaiResolveDispute,
            RESOLVE_DISPUTE_RESPONSE,
            run_kwargs={
                "instrument_id": "aaaa-bbbb-cccc-dddd",
                "resolution": "uphold",
            },
        )
        assert result["resolution"] == "uphold"
        body = mock.post.call_args.kwargs["json"]
        assert body["resolution"] == "uphold"

    def test_resolve_with_evidence(self):
        result, mock = _patch_and_run(
            KagikaiResolveDispute,
            RESOLVE_DISPUTE_RESPONSE,
            run_kwargs={
                "instrument_id": "aaaa-bbbb-cccc-dddd",
                "resolution": "reject",
                "evidence": "https://example.com/counter-proof",
            },
        )
        body = mock.post.call_args.kwargs["json"]
        assert body["evidence"] == "https://example.com/counter-proof"
