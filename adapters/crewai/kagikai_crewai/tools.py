"""29 CrewAI BaseTool subclasses wrapping the Kagikai ICS API."""

import json
from typing import Any, Dict, List

from crewai.tools import BaseTool

from kagikai_crewai._http import KagikaiAPI


# ── Helper ─────────────────────────────────────────────────────────────


def _j(data: Any) -> str:
    return json.dumps(data, indent=2)


# ── Tools ──────────────────────────────────────────────────────────────


class KagikaiHealthTool(BaseTool):
    name: str = "kagikai_health"
    description: str = (
        "Check Kagikai server health. Returns network, Bitcoin node reachability, "
        "and Nostr relay count. No auth required."
    )
    api: KagikaiAPI

    def _run(self) -> str:
        return _j(self.api.get("/health", auth=False))


class KagikaiCreateInstrumentTool(BaseTool):
    name: str = "kagikai_create_instrument"
    description: str = (
        "Create a Kagikai bearer instrument (Bitcoin escrow). Generates a P2TR address. "
        "The issuer key is deleted before funding, making it unconditionally spendable "
        "by the bearer only. Args: amount_sats (int, 2000-100000000), "
        "agent_x25519_pubkey (str, 64-char hex), job_id (str, optional), "
        "locktime_blocks (int, optional, 0 means not set)."
    )
    api: KagikaiAPI

    def _run(
        self,
        amount_sats: int = 0,
        agent_x25519_pubkey: str = "",
        job_id: str = "",
        locktime_blocks: int = 0,
    ) -> str:
        body: Dict[str, Any] = {
            "amount_sats": amount_sats,
            "agent_x25519_pubkey": agent_x25519_pubkey,
            "job_id": job_id,
        }
        if locktime_blocks > 0:
            body["locktime_blocks"] = locktime_blocks
        return _j(self.api.post("/v1/instrument/create", body))


class KagikaiConfirmInstrumentTool(BaseTool):
    name: str = "kagikai_confirm_instrument"
    description: str = (
        "Confirm an instrument after funding. Args: instrument_id (str, UUID), "
        "txid (str, 64-char hex Bitcoin txid)."
    )
    api: KagikaiAPI

    def _run(
        self,
        instrument_id: str = "",
        txid: str = "",
    ) -> str:
        return _j(self.api.post("/v1/instrument/confirm", {
            "instrument_id": instrument_id,
            "txid": txid,
        }))


class KagikaiVerifyAddressTool(BaseTool):
    name: str = "kagikai_verify_address"
    description: str = (
        "Verify a Bitcoin address has sufficient funds via dual-node verification. "
        "Args: address (str), expected_sats (int)."
    )
    api: KagikaiAPI

    def _run(
        self,
        address: str = "",
        expected_sats: int = 0,
    ) -> str:
        return _j(self.api.post("/v1/verify", {
            "address": address,
            "expected_sats": expected_sats,
        }))


class KagikaiGetAttestationTool(BaseTool):
    name: str = "kagikai_get_attestation"
    description: str = (
        "Get attestation document for an instrument. In TDX mode, includes "
        "hardware-rooted proof of issuer key deletion. No auth required. "
        "Args: instrument_id (str, UUID)."
    )
    api: KagikaiAPI

    def _run(self, instrument_id: str = "") -> str:
        return _j(self.api.get(f"/v1/attestation/{instrument_id}", auth=False))


class KagikaiGetStatusTool(BaseTool):
    name: str = "kagikai_get_status"
    description: str = (
        "Get current instrument status: created, watching_for_funding, forwarding, "
        "confirmed, submitted, dispute_window, disputed, completed, rejected, expired, "
        "available, refunding, refunded, swept. Args: instrument_id (str, UUID)."
    )
    api: KagikaiAPI

    def _run(self, instrument_id: str = "") -> str:
        return _j(self.api.get(f"/v1/instrument/{instrument_id}/status"))


class KagikaiCreateBatchTool(BaseTool):
    name: str = "kagikai_batch_create"
    description: str = (
        "Create multiple instruments in one call. Max 20 per batch. "
        "Args: instruments (list of {amount_sats, label?}), "
        "agent_x25519_pubkey (str, 64-char hex), job_id (str, optional)."
    )
    api: KagikaiAPI

    def _run(
        self,
        instruments: str = "[]",
        agent_x25519_pubkey: str = "",
        job_id: str = "",
    ) -> str:
        # CrewAI passes args as strings; parse JSON list
        if isinstance(instruments, str):
            parsed = json.loads(instruments)
        else:
            parsed = instruments
        body: Dict[str, Any] = {
            "instruments": parsed,
            "agent_x25519_pubkey": agent_x25519_pubkey,
        }
        if job_id:
            body["job_id"] = job_id
        return _j(self.api.post("/v1/batch/create", body))


class KagikaiGetBatchStatusTool(BaseTool):
    name: str = "kagikai_batch_status"
    description: str = (
        "Get status of all instruments in a batch. "
        "Args: batch_id (str, UUID)."
    )
    api: KagikaiAPI

    def _run(self, batch_id: str = "") -> str:
        return _j(self.api.get(f"/v1/batch/{batch_id}/status"))


class KagikaiWatchReceiptTool(BaseTool):
    name: str = "kagikai_watch_receipt"
    description: str = (
        "Watch Nostr relays for a transfer receipt. Forwards to webhook URL. "
        "Expires after 600 seconds. Args: instrument_id (str), nonce_hex (str, 64-char), "
        "kb_pubkey_hex (str, 64-char), webhook_url (str, HTTPS)."
    )
    api: KagikaiAPI

    def _run(
        self,
        instrument_id: str = "",
        nonce_hex: str = "",
        kb_pubkey_hex: str = "",
        webhook_url: str = "",
    ) -> str:
        return _j(self.api.post("/v1/receipt/watch", {
            "instrument_id": instrument_id,
            "nonce_hex": nonce_hex,
            "kb_pubkey_hex": kb_pubkey_hex,
            "webhook_url": webhook_url,
        }))


class KagikaiDeleteWatchTool(BaseTool):
    name: str = "kagikai_delete_watch"
    description: str = (
        "Cancel an active receipt watch and close its Nostr subscriptions. "
        "Args: watch_id (str, UUID)."
    )
    api: KagikaiAPI

    def _run(self, watch_id: str = "") -> str:
        return _j(self.api.delete(f"/v1/receipt/watch/{watch_id}"))


class KagikaiGetAgentTool(BaseTool):
    name: str = "kagikai_get_agent"
    description: str = (
        "Get agent identity and reputation. No auth required. "
        "Args: pubkey_hex (str, 64-char hex)."
    )
    api: KagikaiAPI

    def _run(self, pubkey_hex: str = "") -> str:
        return _j(self.api.get(f"/v1/agent/{pubkey_hex}", auth=False))


class KagikaiUpdateAgentTool(BaseTool):
    name: str = "kagikai_update_agent"
    description: str = (
        "Update agent profile (display name, capabilities, URL). Authenticated. "
        "Args: pubkey_hex (str, 64-char hex), display_name (str, optional, empty=skip), "
        "capabilities (str, JSON array, optional, empty=skip), url (str, optional, empty=skip)."
    )
    api: KagikaiAPI

    def _run(
        self,
        pubkey_hex: str = "",
        display_name: str = "",
        capabilities: str = "",
        url: str = "",
    ) -> str:
        body: Dict[str, Any] = {}
        if display_name:
            body["display_name"] = display_name
        if capabilities:
            # Accept JSON string or comma-separated
            if capabilities.startswith("["):
                body["capabilities"] = json.loads(capabilities)
            else:
                body["capabilities"] = [c.strip() for c in capabilities.split(",")]
        if url:
            body["url"] = url
        return _j(self.api.put(f"/v1/agent/{pubkey_hex}", body))


class KagikaiGetAgentCardTool(BaseTool):
    name: str = "kagikai_get_agent_card"
    description: str = (
        "Get a Google A2A-compatible Agent Card for discovery. No auth required. "
        "Args: pubkey_hex (str, 64-char hex)."
    )
    api: KagikaiAPI

    def _run(self, pubkey_hex: str = "") -> str:
        return _j(self.api.get(f"/v1/agent/{pubkey_hex}/agent.json", auth=False))


class KagikaiGetReputationTool(BaseTool):
    name: str = "kagikai_get_reputation"
    description: str = (
        "Get reputation stats: instruments created, received, transferred, "
        "disputed, and completion ratio. No auth required. "
        "Args: pubkey_hex (str, 64-char hex)."
    )
    api: KagikaiAPI

    def _run(self, pubkey_hex: str = "") -> str:
        return _j(self.api.get(f"/v1/reputation/{pubkey_hex}", auth=False))


class KagikaiSubmitInstrumentTool(BaseTool):
    name: str = "kagikai_submit_instrument"
    description: str = (
        "Submit deliverable evidence for a confirmed instrument. "
        "If a hash_match evaluator is set, auto-evaluation runs inline. "
        "Args: instrument_id (str, UUID), evidence (str, max 2048 chars)."
    )
    api: KagikaiAPI

    def _run(
        self,
        instrument_id: str = "",
        evidence: str = "",
    ) -> str:
        return _j(self.api.post("/v1/instrument/submit", {
            "instrument_id": instrument_id,
            "evidence": evidence,
        }))


class KagikaiCompleteInstrumentTool(BaseTool):
    name: str = "kagikai_complete_instrument"
    description: str = (
        "Mark a submitted instrument as completed. Bearer may sweep funds after. "
        "Args: instrument_id (str, UUID)."
    )
    api: KagikaiAPI

    def _run(self, instrument_id: str = "") -> str:
        return _j(self.api.post("/v1/instrument/complete", {
            "instrument_id": instrument_id,
        }))


class KagikaiRejectInstrumentTool(BaseTool):
    name: str = "kagikai_reject_instrument"
    description: str = (
        "Reject a submitted instrument with optional reason. "
        "Args: instrument_id (str, UUID), reason (str, optional, max 512 chars)."
    )
    api: KagikaiAPI

    def _run(
        self,
        instrument_id: str = "",
        reason: str = "",
    ) -> str:
        body: Dict[str, Any] = {"instrument_id": instrument_id}
        if reason:
            body["reason"] = reason
        return _j(self.api.post("/v1/instrument/reject", body))


class KagikaiVerifyTdxQuoteTool(BaseTool):
    name: str = "kagikai_verify_tdx_quote"
    description: str = (
        "Structurally verify the TDX quote in an attestation. Checks quote header "
        "(TDX v4), Intel vendor ID, and REPORTDATA code_hash match. "
        "Args: instrument_id (str, UUID), expected_code_hash (str, optional, empty=skip)."
    )
    api: KagikaiAPI

    def _run(
        self,
        instrument_id: str = "",
        expected_code_hash: str = "",
    ) -> str:
        attestation = self.api.get(f"/v1/attestation/{instrument_id}", auth=False)
        try:
            from kagikai.tdx_verify import verify_tdx_attestation
            result = verify_tdx_attestation(
                attestation,
                expected_code_hash=expected_code_hash if expected_code_hash else None,
            )
            return _j({
                "valid": result.valid,
                "code_hash_match": result.code_hash_match,
                "error": result.error,
                "quote_version": result.quote_info.version if result.quote_info else None,
                "quote_tee_type": (
                    hex(result.quote_info.tee_type) if result.quote_info else None
                ),
                "quote_size": result.quote_info.quote_size if result.quote_info else None,
                "code_hash_from_report": (
                    result.quote_info.code_hash_from_report if result.quote_info else None
                ),
            })
        except ImportError:
            return _j({
                "error": "Install kagikai SDK for TDX verification: pip install kagikai",
                "attestation": attestation,
            })


# ── Phase 10: Escrow tools ────────────────────────────────────────────


class KagikaiEscrowCreateTool(BaseTool):
    name: str = "kagikai_escrow_create"
    description: str = (
        "Create a new escrow: ICS-native instrument with auto-sweep. "
        "Args: amount_sats (int, min 2000), payee_address (str, Bitcoin address), "
        "description (str, optional), timeout_blocks (int, optional), "
        "evaluator_type (str, optional), evaluator_config (str, JSON, optional)."
    )
    api: KagikaiAPI

    def _run(
        self,
        amount_sats: int = 0,
        payee_address: str = "",
        description: str = "",
        timeout_blocks: int = 0,
        evaluator_type: str = "",
        evaluator_config: str = "",
    ) -> str:
        create_body: Dict[str, Any] = {"amount_sats": amount_sats}
        if timeout_blocks > 0:
            create_body["timeout_blocks"] = timeout_blocks
        if evaluator_type:
            create_body["evaluator_type"] = evaluator_type
        if evaluator_config:
            create_body["evaluator_config"] = json.loads(evaluator_config) if isinstance(evaluator_config, str) else evaluator_config
        ics_resp = self.api.post("/v1/instrument/create", create_body)
        instrument_id = ics_resp["instrument_id"]
        funding_address = ics_resp.get("funding_address", ics_resp["p2tr_address"])
        self.api.post("/v1/instrument/set-destination", {
            "instrument_id": instrument_id,
            "destination_address": payee_address,
        })
        return _j({
            "escrow_id": instrument_id,
            "funding_address": funding_address,
            "p2tr_address": ics_resp["p2tr_address"],
            "amount_sats": amount_sats,
            "fee_sats": ics_resp.get("fee_sats", 0),
            "status": "watching_for_funding",
            "payee_address": payee_address,
            "description": description,
        })


class KagikaiEscrowStatusTool(BaseTool):
    name: str = "kagikai_escrow_status"
    description: str = (
        "Check escrow status. Returns ICS instrument state. "
        "Args: instrument_id (str, UUID)."
    )
    api: KagikaiAPI

    def _run(self, instrument_id: str = "") -> str:
        return _j(self.api.get(f"/v1/instrument/{instrument_id}/status"))


class KagikaiEscrowReleaseTool(BaseTool):
    name: str = "kagikai_escrow_release"
    description: str = (
        "Release an escrow: submit evidence triggering evaluation and auto-sweep. "
        "Args: instrument_id (str, UUID), evidence (str)."
    )
    api: KagikaiAPI

    def _run(self, instrument_id: str = "", evidence: str = "") -> str:
        return _j(self.api.post("/v1/instrument/submit", {
            "instrument_id": instrument_id,
            "evidence": evidence,
        }))


class KagikaiEscrowCancelTool(BaseTool):
    name: str = "kagikai_escrow_cancel"
    description: str = (
        "Cancel/reject an escrow with optional reason. "
        "Args: instrument_id (str, UUID), reason (str, optional)."
    )
    api: KagikaiAPI

    def _run(self, instrument_id: str = "", reason: str = "") -> str:
        body: Dict[str, Any] = {"instrument_id": instrument_id}
        if reason:
            body["reason"] = reason
        return _j(self.api.post("/v1/instrument/reject", body))


# ── Phase 10.5: Destination management ─────────────────────────────────


class KagikaiSetDestinationTool(BaseTool):
    name: str = "kagikai_set_destination"
    description: str = (
        "Set or change the sweep destination for an ICS-native instrument. "
        "Args: instrument_id (str, UUID), destination_address (str, Bitcoin address)."
    )
    api: KagikaiAPI

    def _run(self, instrument_id: str = "", destination_address: str = "") -> str:
        return _j(self.api.post("/v1/instrument/set-destination", {
            "instrument_id": instrument_id,
            "destination_address": destination_address,
        }))


# ── Phase 11: Vault tools ─────────────────────────────────────────────


class KagikaiListAvailableTool(BaseTool):
    name: str = "kagikai_list_available"
    description: str = (
        "List available (vault) instruments for the authenticated creator."
    )
    api: KagikaiAPI

    def _run(self) -> str:
        return _j(self.api.get("/v1/instruments/available"))


class KagikaiRecycleInstrumentTool(BaseTool):
    name: str = "kagikai_recycle_instrument"
    description: str = (
        "Recycle an available instrument: reset to Confirmed with new parameters. "
        "Args: instrument_id (str, UUID), timeout_blocks (int, optional), "
        "evaluator_type (str, optional), evaluator_config (str, JSON, optional)."
    )
    api: KagikaiAPI

    def _run(
        self,
        instrument_id: str = "",
        timeout_blocks: int = 0,
        evaluator_type: str = "",
        evaluator_config: str = "",
    ) -> str:
        body: Dict[str, Any] = {}
        if timeout_blocks > 0:
            body["timeout_blocks"] = timeout_blocks
        if evaluator_type:
            body["evaluator_type"] = evaluator_type
        if evaluator_config:
            body["evaluator_config"] = json.loads(evaluator_config) if isinstance(evaluator_config, str) else evaluator_config
        return _j(self.api.post(f"/v1/instrument/{instrument_id}/recycle", body))


class KagikaiRefundInstrumentTool(BaseTool):
    name: str = "kagikai_refund_instrument"
    description: str = (
        "Refund an available instrument: sweep funds back to the creator's source address. "
        "Args: instrument_id (str, UUID)."
    )
    api: KagikaiAPI

    def _run(self, instrument_id: str = "") -> str:
        return _j(self.api.post(f"/v1/instrument/{instrument_id}/refund", {}))


class KagikaiFeeEstimateTool(BaseTool):
    name: str = "kagikai_fee_estimate"
    description: str = (
        "Estimate fees for an escrow amount. Returns platform fee, mining fees, "
        "and net amount to recipient. Args: amount_sats (int)."
    )
    api: KagikaiAPI

    def _run(self, amount_sats: int = 0) -> str:
        try:
            cfg = self.api.get("/admin/fee-config", auth=True)
            bps = cfg.get("fee_basis_points", 0)
            fee_min = cfg.get("fee_min_sats", 10)
            fee_max = cfg.get("fee_max_sats", 100000)
        except Exception:
            bps, fee_min, fee_max = 100, 10, 100000
        raw_fee = (amount_sats * bps) // 10000
        platform_fee = max(min(raw_fee, fee_max), fee_min) if bps > 0 else 0
        mining_total = 110 * 2 + 111 * 2
        return _j({
            "amount_sats": amount_sats,
            "platform_fee_sats": platform_fee,
            "mining_fee_total_sats": mining_total,
            "total_cost_sats": platform_fee + mining_total,
            "net_to_recipient_sats": amount_sats - platform_fee - mining_total,
        })


# ── Phase 14: Dispute tools ───────────────────────────────────────────


class KagikaiDisputeInstrumentTool(BaseTool):
    name: str = "kagikai_dispute_instrument"
    description: str = (
        "Dispute an instrument in DisputeWindow status. Posts a bond to challenge delivery. "
        "Args: instrument_id (str, UUID), reason (str, max 1024 chars)."
    )
    api: KagikaiAPI

    def _run(self, instrument_id: str = "", reason: str = "") -> str:
        return _j(self.api.post("/v1/instrument/dispute", {
            "instrument_id": instrument_id,
            "reason": reason,
        }))


class KagikaiResolveDisputeTool(BaseTool):
    name: str = "kagikai_resolve_dispute"
    description: str = (
        "Resolve a disputed instrument: uphold (buyer wins), reject (seller wins), "
        "or refund (seller voluntary). "
        "Args: instrument_id (str, UUID), resolution (str: uphold/reject/refund), "
        "evidence (str, optional)."
    )
    api: KagikaiAPI

    def _run(
        self,
        instrument_id: str = "",
        resolution: str = "",
        evidence: str = "",
    ) -> str:
        body: Dict[str, Any] = {
            "instrument_id": instrument_id,
            "resolution": resolution,
        }
        if evidence:
            body["evidence"] = evidence
        return _j(self.api.post("/v1/instrument/resolve", body))


# ── Factory ────────────────────────────────────────────────────────────


def kagikai_tools(base_url: str = "", api_key: str = "") -> List[BaseTool]:
    """Create all 29 Kagikai tools with shared API configuration.

    Usage::

        from kagikai_crewai import kagikai_tools
        tools = kagikai_tools(base_url="https://...", api_key="...")

    Environment variables ``KAGIKAI_BASE_URL`` and ``KAGIKAI_API_KEY`` are
    used as fallbacks when args are empty.
    """
    api = KagikaiAPI(base_url=base_url, api_key=api_key)
    return [
        KagikaiHealthTool(api=api),
        KagikaiCreateInstrumentTool(api=api),
        KagikaiConfirmInstrumentTool(api=api),
        KagikaiVerifyAddressTool(api=api),
        KagikaiGetAttestationTool(api=api),
        KagikaiGetStatusTool(api=api),
        KagikaiCreateBatchTool(api=api),
        KagikaiGetBatchStatusTool(api=api),
        KagikaiWatchReceiptTool(api=api),
        KagikaiDeleteWatchTool(api=api),
        KagikaiGetAgentTool(api=api),
        KagikaiUpdateAgentTool(api=api),
        KagikaiGetAgentCardTool(api=api),
        KagikaiGetReputationTool(api=api),
        KagikaiSubmitInstrumentTool(api=api),
        KagikaiCompleteInstrumentTool(api=api),
        KagikaiRejectInstrumentTool(api=api),
        KagikaiVerifyTdxQuoteTool(api=api),
        KagikaiEscrowCreateTool(api=api),
        KagikaiEscrowStatusTool(api=api),
        KagikaiEscrowReleaseTool(api=api),
        KagikaiEscrowCancelTool(api=api),
        KagikaiSetDestinationTool(api=api),
        KagikaiListAvailableTool(api=api),
        KagikaiRecycleInstrumentTool(api=api),
        KagikaiRefundInstrumentTool(api=api),
        KagikaiFeeEstimateTool(api=api),
        KagikaiDisputeInstrumentTool(api=api),
        KagikaiResolveDisputeTool(api=api),
    ]
