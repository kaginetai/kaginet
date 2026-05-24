"""Tests for kagikai-crewai: all 29 tools + factory with mocked HTTP."""

import json
from unittest.mock import MagicMock, patch

import pytest

# Add adapter paths so imports work without pip install
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "crewai"))

from kagikai_crewai._http import KagikaiAPI
from kagikai_crewai.tools import (
    KagikaiHealthTool,
    KagikaiCreateInstrumentTool,
    KagikaiConfirmInstrumentTool,
    KagikaiVerifyAddressTool,
    KagikaiGetAttestationTool,
    KagikaiGetStatusTool,
    KagikaiCreateBatchTool,
    KagikaiGetBatchStatusTool,
    KagikaiWatchReceiptTool,
    KagikaiDeleteWatchTool,
    KagikaiGetAgentTool,
    KagikaiUpdateAgentTool,
    KagikaiGetAgentCardTool,
    KagikaiGetReputationTool,
    KagikaiSubmitInstrumentTool,
    KagikaiCompleteInstrumentTool,
    KagikaiRejectInstrumentTool,
    KagikaiVerifyTdxQuoteTool,
    KagikaiEscrowCreateTool,
    KagikaiEscrowStatusTool,
    KagikaiEscrowReleaseTool,
    KagikaiEscrowCancelTool,
    KagikaiSetDestinationTool,
    KagikaiListAvailableTool,
    KagikaiRecycleInstrumentTool,
    KagikaiRefundInstrumentTool,
    KagikaiFeeEstimateTool,
    KagikaiDisputeInstrumentTool,
    KagikaiResolveDisputeTool,
    kagikai_tools,
)

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


def _mock_api(response_data: dict):
    """Create KagikaiAPI with mocked httpx.Client returning response_data."""
    api = KagikaiAPI(base_url="http://test-server", api_key="test-key")
    mock_client = MagicMock()
    mock_response = FakeResponse(response_data)
    mock_client.get.return_value = mock_response
    mock_client.post.return_value = mock_response
    mock_client.put.return_value = mock_response
    mock_client.delete.return_value = mock_response
    return api, mock_client


def _patch_and_run(tool_cls, response_data: dict, run_kwargs=None, **tool_kwargs):
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
    def test_constructor_from_args(self):
        api = KagikaiAPI(base_url="http://x", api_key="k")
        assert api.base_url == "http://x"

    def test_constructor_from_env(self, monkeypatch):
        monkeypatch.setenv("KAGIKAI_BASE_URL", "http://env-url")
        monkeypatch.setenv("KAGIKAI_API_KEY", "env-key")
        api = KagikaiAPI()
        assert api.base_url == "http://env-url"


class TestHealth:
    def test_health(self):
        result, mock = _patch_and_run(KagikaiHealthTool, HEALTH_RESPONSE)
        assert result["status"] == "ok"
        mock.get.assert_called_once()


class TestCreateInstrument:
    def test_create(self):
        result, mock = _patch_and_run(
            KagikaiCreateInstrumentTool,
            CREATE_RESPONSE,
            run_kwargs={
                "amount_sats": 50000,
                "agent_x25519_pubkey": "aa" * 32,
            },
        )
        assert result["instrument_id"] == "aaaa-bbbb-cccc-dddd"

    def test_create_with_locktime(self):
        result, mock = _patch_and_run(
            KagikaiCreateInstrumentTool,
            CREATE_RESPONSE,
            run_kwargs={
                "amount_sats": 50000,
                "agent_x25519_pubkey": "aa" * 32,
                "locktime_blocks": 72,
            },
        )
        body = mock.post.call_args.kwargs["json"]
        assert body["locktime_blocks"] == 72

    def test_create_without_locktime(self):
        result, mock = _patch_and_run(
            KagikaiCreateInstrumentTool,
            CREATE_RESPONSE,
            run_kwargs={
                "amount_sats": 50000,
                "agent_x25519_pubkey": "aa" * 32,
            },
        )
        body = mock.post.call_args.kwargs["json"]
        assert "locktime_blocks" not in body


class TestConfirmInstrument:
    def test_confirm(self):
        result, mock = _patch_and_run(
            KagikaiConfirmInstrumentTool,
            CONFIRM_RESPONSE,
            run_kwargs={
                "instrument_id": "aaaa-bbbb-cccc-dddd",
                "txid": "ff" * 32,
            },
        )
        assert result["status"] == "confirmed"


class TestVerifyAddress:
    def test_verify(self):
        result, mock = _patch_and_run(
            KagikaiVerifyAddressTool,
            VERIFY_RESPONSE,
            run_kwargs={
                "address": "bc1p" + "a" * 58,
                "expected_sats": 50000,
            },
        )
        assert result["nodes_agree"] is True


class TestGetAttestation:
    def test_attestation(self):
        result, mock = _patch_and_run(
            KagikaiGetAttestationTool,
            ATTESTATION_RESPONSE,
            run_kwargs={"instrument_id": "aaaa-bbbb-cccc-dddd"},
        )
        assert result["attestation_type"] == "local"


class TestGetStatus:
    def test_status(self):
        result, mock = _patch_and_run(
            KagikaiGetStatusTool,
            STATUS_RESPONSE,
            run_kwargs={"instrument_id": "aaaa-bbbb-cccc-dddd"},
        )
        assert result["status"] == "confirmed"


class TestBatchCreate:
    def test_batch_create(self):
        # CrewAI tools receive strings; pass JSON string
        result, mock = _patch_and_run(
            KagikaiCreateBatchTool,
            BATCH_CREATE_RESPONSE,
            run_kwargs={
                "instruments": json.dumps([{"amount_sats": 10000}, {"amount_sats": 20000}]),
                "agent_x25519_pubkey": "aa" * 32,
            },
        )
        assert result["batch_id"] == "bbbb-1111-2222-3333"


class TestBatchStatus:
    def test_batch_status(self):
        result, mock = _patch_and_run(
            KagikaiGetBatchStatusTool,
            BATCH_STATUS_RESPONSE,
            run_kwargs={"batch_id": "bbbb-1111-2222-3333"},
        )
        assert len(result["instruments"]) == 2


class TestWatchReceipt:
    def test_watch(self):
        result, mock = _patch_and_run(
            KagikaiWatchReceiptTool,
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
    def test_delete(self):
        result, mock = _patch_and_run(
            KagikaiDeleteWatchTool,
            DELETE_WATCH_RESPONSE,
            run_kwargs={"watch_id": "wwww-1111-2222-3333"},
        )
        assert result["status"] == "deleted"
        mock.delete.assert_called_once()


class TestGetAgent:
    def test_agent(self):
        result, mock = _patch_and_run(
            KagikaiGetAgentTool,
            AGENT_RESPONSE,
            run_kwargs={"pubkey_hex": "aa" * 32},
        )
        assert result["display_name"] == "TestAgent"


class TestUpdateAgent:
    def test_update(self):
        result, mock = _patch_and_run(
            KagikaiUpdateAgentTool,
            UPDATE_AGENT_RESPONSE,
            run_kwargs={
                "pubkey_hex": "aa" * 32,
                "display_name": "NewName",
            },
        )
        mock.put.assert_called_once()

    def test_update_empty_body(self):
        """When no optional fields given, body should be empty."""
        result, mock = _patch_and_run(
            KagikaiUpdateAgentTool,
            UPDATE_AGENT_RESPONSE,
            run_kwargs={"pubkey_hex": "aa" * 32},
        )
        body = mock.put.call_args.kwargs["json"]
        assert body == {}

    def test_update_capabilities_json(self):
        """Capabilities passed as JSON array string."""
        result, mock = _patch_and_run(
            KagikaiUpdateAgentTool,
            UPDATE_AGENT_RESPONSE,
            run_kwargs={
                "pubkey_hex": "aa" * 32,
                "capabilities": '["payment", "escrow"]',
            },
        )
        body = mock.put.call_args.kwargs["json"]
        assert body["capabilities"] == ["payment", "escrow"]


class TestGetAgentCard:
    def test_agent_card(self):
        result, mock = _patch_and_run(
            KagikaiGetAgentCardTool,
            AGENT_CARD_RESPONSE,
            run_kwargs={"pubkey_hex": "aa" * 32},
        )
        assert result["name"] == "TestAgent"


class TestGetReputation:
    def test_reputation(self):
        result, mock = _patch_and_run(
            KagikaiGetReputationTool,
            REPUTATION_RESPONSE,
            run_kwargs={"pubkey_hex": "aa" * 32},
        )
        assert result["instruments_created"] == 10


class TestSubmitInstrument:
    def test_submit(self):
        result, mock = _patch_and_run(
            KagikaiSubmitInstrumentTool,
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
            KagikaiCompleteInstrumentTool,
            COMPLETE_RESPONSE,
            run_kwargs={"instrument_id": "aaaa-bbbb-cccc-dddd"},
        )
        assert result["status"] == "completed"


class TestRejectInstrument:
    def test_reject_with_reason(self):
        result, mock = _patch_and_run(
            KagikaiRejectInstrumentTool,
            REJECT_RESPONSE,
            run_kwargs={
                "instrument_id": "aaaa-bbbb-cccc-dddd",
                "reason": "bad deliverable",
            },
        )
        body = mock.post.call_args.kwargs["json"]
        assert body["reason"] == "bad deliverable"

    def test_reject_without_reason(self):
        result, mock = _patch_and_run(
            KagikaiRejectInstrumentTool,
            REJECT_RESPONSE,
            run_kwargs={"instrument_id": "aaaa-bbbb-cccc-dddd"},
        )
        body = mock.post.call_args.kwargs["json"]
        assert "reason" not in body


class TestVerifyTdxQuote:
    def test_tdx_no_sdk(self):
        api, mock_client = _mock_api(ATTESTATION_RESPONSE)
        with patch("httpx.Client") as mock_cls:
            mock_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
            mock_cls.return_value.__exit__ = MagicMock(return_value=False)
            tool = KagikaiVerifyTdxQuoteTool(api=api)
            with patch.dict("sys.modules", {"kagikai": None, "kagikai.tdx_verify": None}):
                result_str = tool._run(instrument_id="aaaa-bbbb-cccc-dddd")
        result = json.loads(result_str)
        assert "error" in result
        assert "kagikai SDK" in result["error"]


class TestFactory:
    def test_factory_returns_29_tools(self):
        tools = kagikai_tools(base_url="http://test", api_key="key")
        assert len(tools) == 29

    def test_factory_tools_share_api(self):
        tools = kagikai_tools(base_url="http://test", api_key="key")
        apis = {id(t.api) for t in tools}
        assert len(apis) == 1

    def test_factory_tool_names_unique(self):
        tools = kagikai_tools(base_url="http://test", api_key="key")
        names = [t.name for t in tools]
        assert len(names) == len(set(names))


class TestHTTPErrors:
    def test_http_error_propagates(self):
        import httpx
        api = KagikaiAPI(base_url="http://test", api_key="key")
        mock_client = MagicMock()
        err_response = FakeResponse({"error": "not found"}, status_code=404)
        mock_client.get.return_value = err_response

        with patch("httpx.Client") as mock_cls:
            mock_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
            mock_cls.return_value.__exit__ = MagicMock(return_value=False)
            tool = KagikaiHealthTool(api=api)
            with pytest.raises(httpx.HTTPStatusError):
                tool._run()


# ── Phase 10/11/14 tool tests ─────────────────────────────────────────


class TestEscrowCreate:
    def test_escrow_create(self):
        # EscrowCreate makes 2 POST calls (create + set-destination)
        # and returns a composite response with escrow_id
        result, mock = _patch_and_run(
            KagikaiEscrowCreateTool,
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
            KagikaiEscrowCreateTool,
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
            KagikaiEscrowStatusTool,
            ESCROW_STATUS_RESPONSE,
            run_kwargs={"instrument_id": "eeee-1111-2222-3333"},
        )
        assert result["status"] == "confirmed"


class TestEscrowRelease:
    def test_escrow_release(self):
        result, mock = _patch_and_run(
            KagikaiEscrowReleaseTool,
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
            KagikaiEscrowCancelTool,
            ESCROW_CANCEL_RESPONSE,
            run_kwargs={
                "instrument_id": "eeee-1111-2222-3333",
                "reason": "buyer cancelled",
            },
        )
        assert result["status"] == "rejected"

    def test_escrow_cancel_no_reason(self):
        result, mock = _patch_and_run(
            KagikaiEscrowCancelTool,
            ESCROW_CANCEL_RESPONSE,
            run_kwargs={"instrument_id": "eeee-1111-2222-3333"},
        )
        body = mock.post.call_args.kwargs["json"]
        assert "reason" not in body


class TestSetDestination:
    def test_set_destination(self):
        result, mock = _patch_and_run(
            KagikaiSetDestinationTool,
            SET_DESTINATION_RESPONSE,
            run_kwargs={
                "instrument_id": "aaaa-bbbb-cccc-dddd",
                "destination_address": "bc1p" + "f" * 58,
            },
        )
        mock.post.assert_called_once()


class TestListAvailable:
    def test_list_available(self):
        result, mock = _patch_and_run(
            KagikaiListAvailableTool,
            LIST_AVAILABLE_RESPONSE,
        )
        assert len(result["instruments"]) == 2
        mock.get.assert_called_once()


class TestRecycleInstrument:
    def test_recycle(self):
        result, mock = _patch_and_run(
            KagikaiRecycleInstrumentTool,
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
            KagikaiRefundInstrumentTool,
            REFUND_RESPONSE,
            run_kwargs={"instrument_id": "aaaa-bbbb-cccc-dddd"},
        )
        assert result["status"] == "refunding"
        mock.post.assert_called_once()


class TestFeeEstimate:
    def test_fee_estimate(self):
        # FeeEstimate fetches /admin/fee-config then computes locally
        result, mock = _patch_and_run(
            KagikaiFeeEstimateTool,
            FEE_ESTIMATE_RESPONSE,
            run_kwargs={"amount_sats": 50000},
        )
        assert result["amount_sats"] == 50000
        assert result["platform_fee_sats"] == 250  # (50000 * 50) / 10000
        assert "net_to_recipient_sats" in result


class TestDisputeInstrument:
    def test_dispute(self):
        result, mock = _patch_and_run(
            KagikaiDisputeInstrumentTool,
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
            KagikaiResolveDisputeTool,
            RESOLVE_DISPUTE_RESPONSE,
            run_kwargs={
                "instrument_id": "aaaa-bbbb-cccc-dddd",
                "resolution": "uphold",
            },
        )
        assert result["resolution"] == "uphold"

    def test_resolve_with_evidence(self):
        result, mock = _patch_and_run(
            KagikaiResolveDisputeTool,
            RESOLVE_DISPUTE_RESPONSE,
            run_kwargs={
                "instrument_id": "aaaa-bbbb-cccc-dddd",
                "resolution": "reject",
                "evidence": "https://example.com/counter-proof",
            },
        )
        body = mock.post.call_args.kwargs["json"]
        assert body["evidence"] == "https://example.com/counter-proof"
