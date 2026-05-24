"""29 LangChain BaseTool subclasses wrapping the Kagikai ICS API."""

from __future__ import annotations

import json
from typing import Any, Optional

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from kagikai_langchain._http import KagikaiAPI


# ── Input schemas ──────────────────────────────────────────────────────


class EmptyInput(BaseModel):
    """No arguments required."""


class CreateInstrumentInput(BaseModel):
    amount_sats: int = Field(description="Amount in satoshis (min 2000, max 100000000)")
    agent_x25519_pubkey: str = Field(description="Agent X25519 public key, 64-char hex")
    job_id: str = Field(default="", description="Optional job identifier")
    locktime_blocks: Optional[int] = Field(default=None, description="Optional locktime in blocks")


class ConfirmInstrumentInput(BaseModel):
    instrument_id: str = Field(description="UUID of the instrument")
    txid: str = Field(description="64-char hex Bitcoin funding txid")


class VerifyAddressInput(BaseModel):
    address: str = Field(description="Bitcoin address to verify")
    expected_sats: int = Field(description="Expected minimum balance in satoshis")


class InstrumentIdInput(BaseModel):
    instrument_id: str = Field(description="UUID of the instrument")


class BatchCreateInput(BaseModel):
    instruments: list[dict[str, Any]] = Field(
        description="List of {amount_sats: int, label?: str} objects"
    )
    agent_x25519_pubkey: str = Field(description="Agent X25519 public key, 64-char hex")
    job_id: str = Field(default="", description="Optional job identifier")


class BatchIdInput(BaseModel):
    batch_id: str = Field(description="UUID of the batch")


class WatchReceiptInput(BaseModel):
    instrument_id: str = Field(description="UUID of the confirmed instrument")
    nonce_hex: str = Field(description="64-char hex session nonce")
    kb_pubkey_hex: str = Field(description="64-char hex x-only pubkey of kB")
    webhook_url: str = Field(description="HTTPS URL for receipt webhook")


class WatchIdInput(BaseModel):
    watch_id: str = Field(description="UUID of the watch to delete")


class PubkeyInput(BaseModel):
    pubkey_hex: str = Field(description="Agent X25519 pubkey, 64-char hex")


class UpdateAgentInput(BaseModel):
    pubkey_hex: str = Field(description="Agent X25519 pubkey, 64-char hex")
    display_name: Optional[str] = Field(default=None, description="Display name (max 128 chars)")
    capabilities: Optional[list[str]] = Field(default=None, description="Capability list")
    url: Optional[str] = Field(default=None, description="Agent endpoint URL (max 512 chars)")


class SubmitInstrumentInput(BaseModel):
    instrument_id: str = Field(description="UUID of the confirmed instrument")
    evidence: str = Field(description="Evidence string (URL, hash, or text, max 2048 chars)")


class RejectInstrumentInput(BaseModel):
    instrument_id: str = Field(description="UUID of the submitted instrument")
    reason: str = Field(default="", description="Optional rejection reason (max 512 chars)")


class VerifyTdxQuoteInput(BaseModel):
    instrument_id: str = Field(description="UUID of the instrument")
    expected_code_hash: Optional[str] = Field(
        default=None, description="Known-good code hash to verify against"
    )


class EscrowCreateInput(BaseModel):
    amount_sats: int = Field(description="Escrow amount in satoshis (min 2000)")
    payee_address: str = Field(description="Bitcoin address to sweep funds to on release")
    description: Optional[str] = Field(default=None, description="Human-readable description")
    timeout_blocks: Optional[int] = Field(default=None, description="Timeout in blocks")
    evaluator_type: Optional[str] = Field(default=None, description="Evaluator type (hash_match, optimistic, etc.)")
    evaluator_config: Optional[dict[str, Any]] = Field(default=None, description="Evaluator config")


class EscrowReleaseInput(BaseModel):
    instrument_id: str = Field(description="UUID of the escrow instrument")
    evidence: str = Field(description="Evidence string for release")


class EscrowCancelInput(BaseModel):
    instrument_id: str = Field(description="UUID of the escrow instrument")
    reason: Optional[str] = Field(default=None, description="Cancellation reason")


class SetDestinationInput(BaseModel):
    instrument_id: str = Field(description="UUID of the instrument")
    destination_address: str = Field(description="Bitcoin address to sweep funds to")


class RecycleInstrumentInput(BaseModel):
    instrument_id: str = Field(description="UUID of the Available instrument")
    timeout_blocks: Optional[int] = Field(default=None, description="New timeout in blocks")
    evaluator_type: Optional[str] = Field(default=None, description="Evaluator type")
    evaluator_config: Optional[dict[str, Any]] = Field(default=None, description="Evaluator config")


class AmountInput(BaseModel):
    amount_sats: int = Field(description="Amount in satoshis")


class DisputeInstrumentInput(BaseModel):
    instrument_id: str = Field(description="UUID of the instrument in DisputeWindow status")
    reason: str = Field(description="Reason for the dispute (max 1024 chars)")


class ResolveDisputeInput(BaseModel):
    instrument_id: str = Field(description="UUID of the disputed instrument")
    resolution: str = Field(description="uphold, reject, or refund")
    evidence: Optional[str] = Field(default=None, description="Evidence for the resolution")


# ── Helper ─────────────────────────────────────────────────────────────


def _j(data: Any) -> str:
    return json.dumps(data, indent=2)


# ── Tools ──────────────────────────────────────────────────────────────


class KagikaiHealth(BaseTool):
    name: str = "kagikai_health"
    description: str = (
        "Check Kagikai server health. Returns network, Bitcoin node reachability, "
        "and Nostr relay count. No auth required."
    )
    args_schema: type[BaseModel] = EmptyInput
    api: KagikaiAPI = Field(exclude=True)

    def _run(self, **_kwargs: Any) -> str:
        return _j(self.api.get("/health", auth=False))


class KagikaiCreateInstrument(BaseTool):
    name: str = "kagikai_create_instrument"
    description: str = (
        "Create a Kagikai bearer instrument (Bitcoin escrow). Generates a P2TR address. "
        "The issuer key is deleted before funding, making it unconditionally spendable "
        "by the bearer only."
    )
    args_schema: type[BaseModel] = CreateInstrumentInput
    api: KagikaiAPI = Field(exclude=True)

    def _run(
        self,
        amount_sats: int,
        agent_x25519_pubkey: str,
        job_id: str = "",
        locktime_blocks: Optional[int] = None,
        **_kwargs: Any,
    ) -> str:
        body: dict[str, Any] = {
            "amount_sats": amount_sats,
            "agent_x25519_pubkey": agent_x25519_pubkey,
            "job_id": job_id,
        }
        if locktime_blocks is not None:
            body["locktime_blocks"] = locktime_blocks
        return _j(self.api.post("/v1/instrument/create", body))


class KagikaiConfirmInstrument(BaseTool):
    name: str = "kagikai_confirm_instrument"
    description: str = (
        "Confirm an instrument after funding. Verifies the UTXO, checks fee output, "
        "and upgrades attestation to full (with TDX quote in TEE mode)."
    )
    args_schema: type[BaseModel] = ConfirmInstrumentInput
    api: KagikaiAPI = Field(exclude=True)

    def _run(self, instrument_id: str, txid: str, **_kwargs: Any) -> str:
        return _j(self.api.post("/v1/instrument/confirm", {
            "instrument_id": instrument_id,
            "txid": txid,
        }))


class KagikaiVerifyAddress(BaseTool):
    name: str = "kagikai_verify_address"
    description: str = (
        "Verify a Bitcoin address has sufficient funds via dual-node verification."
    )
    args_schema: type[BaseModel] = VerifyAddressInput
    api: KagikaiAPI = Field(exclude=True)

    def _run(self, address: str, expected_sats: int, **_kwargs: Any) -> str:
        return _j(self.api.post("/v1/verify", {
            "address": address,
            "expected_sats": expected_sats,
        }))


class KagikaiGetAttestation(BaseTool):
    name: str = "kagikai_get_attestation"
    description: str = (
        "Get attestation document for an instrument. In TDX mode, includes "
        "hardware-rooted proof of issuer key deletion. No auth required."
    )
    args_schema: type[BaseModel] = InstrumentIdInput
    api: KagikaiAPI = Field(exclude=True)

    def _run(self, instrument_id: str, **_kwargs: Any) -> str:
        return _j(self.api.get(f"/v1/attestation/{instrument_id}", auth=False))


class KagikaiGetStatus(BaseTool):
    name: str = "kagikai_get_status"
    description: str = (
        "Get current instrument status: created, watching_for_funding, forwarding, "
        "confirmed, submitted, dispute_window, disputed, completed, rejected, expired, "
        "available, refunding, refunded, swept."
    )
    args_schema: type[BaseModel] = InstrumentIdInput
    api: KagikaiAPI = Field(exclude=True)

    def _run(self, instrument_id: str, **_kwargs: Any) -> str:
        return _j(self.api.get(f"/v1/instrument/{instrument_id}/status"))


class KagikaiCreateBatch(BaseTool):
    name: str = "kagikai_batch_create"
    description: str = (
        "Create multiple instruments in one call. Each gets its own P2TR address. "
        "One TDX attestation covers the batch. Max 20 per batch."
    )
    args_schema: type[BaseModel] = BatchCreateInput
    api: KagikaiAPI = Field(exclude=True)

    def _run(
        self,
        instruments: list[dict[str, Any]],
        agent_x25519_pubkey: str,
        job_id: str = "",
        **_kwargs: Any,
    ) -> str:
        body: dict[str, Any] = {
            "instruments": instruments,
            "agent_x25519_pubkey": agent_x25519_pubkey,
        }
        if job_id:
            body["job_id"] = job_id
        return _j(self.api.post("/v1/batch/create", body))


class KagikaiGetBatchStatus(BaseTool):
    name: str = "kagikai_batch_status"
    description: str = "Get status of all instruments in a batch."
    args_schema: type[BaseModel] = BatchIdInput
    api: KagikaiAPI = Field(exclude=True)

    def _run(self, batch_id: str, **_kwargs: Any) -> str:
        return _j(self.api.get(f"/v1/batch/{batch_id}/status"))


class KagikaiWatchReceipt(BaseTool):
    name: str = "kagikai_watch_receipt"
    description: str = (
        "Watch Nostr relays for a transfer receipt. Forwards to webhook URL. "
        "Expires after 600 seconds."
    )
    args_schema: type[BaseModel] = WatchReceiptInput
    api: KagikaiAPI = Field(exclude=True)

    def _run(
        self,
        instrument_id: str,
        nonce_hex: str,
        kb_pubkey_hex: str,
        webhook_url: str,
        **_kwargs: Any,
    ) -> str:
        return _j(self.api.post("/v1/receipt/watch", {
            "instrument_id": instrument_id,
            "nonce_hex": nonce_hex,
            "kb_pubkey_hex": kb_pubkey_hex,
            "webhook_url": webhook_url,
        }))


class KagikaiDeleteWatch(BaseTool):
    name: str = "kagikai_delete_watch"
    description: str = "Cancel an active receipt watch and close its Nostr subscriptions."
    args_schema: type[BaseModel] = WatchIdInput
    api: KagikaiAPI = Field(exclude=True)

    def _run(self, watch_id: str, **_kwargs: Any) -> str:
        return _j(self.api.delete(f"/v1/receipt/watch/{watch_id}"))


class KagikaiGetAgent(BaseTool):
    name: str = "kagikai_get_agent"
    description: str = (
        "Get agent identity and reputation. Agents register on first instrument creation. "
        "No auth required."
    )
    args_schema: type[BaseModel] = PubkeyInput
    api: KagikaiAPI = Field(exclude=True)

    def _run(self, pubkey_hex: str, **_kwargs: Any) -> str:
        return _j(self.api.get(f"/v1/agent/{pubkey_hex}", auth=False))


class KagikaiUpdateAgent(BaseTool):
    name: str = "kagikai_update_agent"
    description: str = (
        "Update agent profile (display name, capabilities, URL). Authenticated."
    )
    args_schema: type[BaseModel] = UpdateAgentInput
    api: KagikaiAPI = Field(exclude=True)

    def _run(
        self,
        pubkey_hex: str,
        display_name: Optional[str] = None,
        capabilities: Optional[list[str]] = None,
        url: Optional[str] = None,
        **_kwargs: Any,
    ) -> str:
        body: dict[str, Any] = {}
        if display_name is not None:
            body["display_name"] = display_name
        if capabilities is not None:
            body["capabilities"] = capabilities
        if url is not None:
            body["url"] = url
        return _j(self.api.put(f"/v1/agent/{pubkey_hex}", body))


class KagikaiGetAgentCard(BaseTool):
    name: str = "kagikai_get_agent_card"
    description: str = (
        "Get a Google A2A-compatible Agent Card for discovery. No auth required."
    )
    args_schema: type[BaseModel] = PubkeyInput
    api: KagikaiAPI = Field(exclude=True)

    def _run(self, pubkey_hex: str, **_kwargs: Any) -> str:
        return _j(self.api.get(f"/v1/agent/{pubkey_hex}/agent.json", auth=False))


class KagikaiGetReputation(BaseTool):
    name: str = "kagikai_get_reputation"
    description: str = (
        "Get reputation stats: instruments created, received, transferred, "
        "disputed, and completion ratio. No auth required."
    )
    args_schema: type[BaseModel] = PubkeyInput
    api: KagikaiAPI = Field(exclude=True)

    def _run(self, pubkey_hex: str, **_kwargs: Any) -> str:
        return _j(self.api.get(f"/v1/reputation/{pubkey_hex}", auth=False))


class KagikaiSubmitInstrument(BaseTool):
    name: str = "kagikai_submit_instrument"
    description: str = (
        "Submit deliverable evidence for a confirmed instrument. "
        "If a hash_match evaluator is set, auto-evaluation runs inline."
    )
    args_schema: type[BaseModel] = SubmitInstrumentInput
    api: KagikaiAPI = Field(exclude=True)

    def _run(self, instrument_id: str, evidence: str, **_kwargs: Any) -> str:
        return _j(self.api.post("/v1/instrument/submit", {
            "instrument_id": instrument_id,
            "evidence": evidence,
        }))


class KagikaiCompleteInstrument(BaseTool):
    name: str = "kagikai_complete_instrument"
    description: str = (
        "Mark a submitted instrument as completed. Bearer may sweep funds after."
    )
    args_schema: type[BaseModel] = InstrumentIdInput
    api: KagikaiAPI = Field(exclude=True)

    def _run(self, instrument_id: str, **_kwargs: Any) -> str:
        return _j(self.api.post("/v1/instrument/complete", {
            "instrument_id": instrument_id,
        }))


class KagikaiRejectInstrument(BaseTool):
    name: str = "kagikai_reject_instrument"
    description: str = "Reject a submitted instrument with optional reason."
    args_schema: type[BaseModel] = RejectInstrumentInput
    api: KagikaiAPI = Field(exclude=True)

    def _run(self, instrument_id: str, reason: str = "", **_kwargs: Any) -> str:
        body: dict[str, Any] = {"instrument_id": instrument_id}
        if reason:
            body["reason"] = reason
        return _j(self.api.post("/v1/instrument/reject", body))


class KagikaiVerifyTdxQuote(BaseTool):
    name: str = "kagikai_verify_tdx_quote"
    description: str = (
        "Structurally verify the TDX quote in an attestation. Checks quote header "
        "(TDX v4), Intel vendor ID, and REPORTDATA code_hash match."
    )
    args_schema: type[BaseModel] = VerifyTdxQuoteInput
    api: KagikaiAPI = Field(exclude=True)

    def _run(
        self,
        instrument_id: str,
        expected_code_hash: Optional[str] = None,
        **_kwargs: Any,
    ) -> str:
        attestation = self.api.get(f"/v1/attestation/{instrument_id}", auth=False)
        try:
            from kagikai.tdx_verify import verify_tdx_attestation
            result = verify_tdx_attestation(
                attestation, expected_code_hash=expected_code_hash
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


class KagikaiEscrowCreate(BaseTool):
    name: str = "kagikai_escrow_create"
    description: str = (
        "Create a new escrow: ICS-native instrument with auto-sweep. "
        "Funds are held in escrow and auto-swept to the payee on release."
    )
    args_schema: type[BaseModel] = EscrowCreateInput
    api: KagikaiAPI = Field(exclude=True)

    def _run(
        self,
        amount_sats: int,
        payee_address: str,
        description: Optional[str] = None,
        timeout_blocks: Optional[int] = None,
        evaluator_type: Optional[str] = None,
        evaluator_config: Optional[dict[str, Any]] = None,
        **_kwargs: Any,
    ) -> str:
        create_body: dict[str, Any] = {"amount_sats": amount_sats}
        if timeout_blocks is not None:
            create_body["timeout_blocks"] = timeout_blocks
        if evaluator_type is not None:
            create_body["evaluator_type"] = evaluator_type
        if evaluator_config is not None:
            create_body["evaluator_config"] = evaluator_config
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
            "description": description or "",
        })


class KagikaiEscrowStatus(BaseTool):
    name: str = "kagikai_escrow_status"
    description: str = "Check escrow status. Returns ICS instrument state."
    args_schema: type[BaseModel] = InstrumentIdInput
    api: KagikaiAPI = Field(exclude=True)

    def _run(self, instrument_id: str, **_kwargs: Any) -> str:
        return _j(self.api.get(f"/v1/instrument/{instrument_id}/status"))


class KagikaiEscrowRelease(BaseTool):
    name: str = "kagikai_escrow_release"
    description: str = (
        "Release an escrow: submit evidence triggering evaluation and auto-sweep."
    )
    args_schema: type[BaseModel] = EscrowReleaseInput
    api: KagikaiAPI = Field(exclude=True)

    def _run(self, instrument_id: str, evidence: str, **_kwargs: Any) -> str:
        return _j(self.api.post("/v1/instrument/submit", {
            "instrument_id": instrument_id,
            "evidence": evidence,
        }))


class KagikaiEscrowCancel(BaseTool):
    name: str = "kagikai_escrow_cancel"
    description: str = "Cancel/reject an escrow with optional reason."
    args_schema: type[BaseModel] = EscrowCancelInput
    api: KagikaiAPI = Field(exclude=True)

    def _run(self, instrument_id: str, reason: Optional[str] = None, **_kwargs: Any) -> str:
        body: dict[str, Any] = {"instrument_id": instrument_id}
        if reason:
            body["reason"] = reason
        return _j(self.api.post("/v1/instrument/reject", body))


# ── Phase 10.5: Destination management ─────────────────────────────────


class KagikaiSetDestination(BaseTool):
    name: str = "kagikai_set_destination"
    description: str = (
        "Set or change the sweep destination for an ICS-native instrument."
    )
    args_schema: type[BaseModel] = SetDestinationInput
    api: KagikaiAPI = Field(exclude=True)

    def _run(self, instrument_id: str, destination_address: str, **_kwargs: Any) -> str:
        return _j(self.api.post("/v1/instrument/set-destination", {
            "instrument_id": instrument_id,
            "destination_address": destination_address,
        }))


# ── Phase 11: Vault tools ─────────────────────────────────────────────


class KagikaiListAvailable(BaseTool):
    name: str = "kagikai_list_available"
    description: str = (
        "List available (vault) instruments for the authenticated creator."
    )
    args_schema: type[BaseModel] = EmptyInput
    api: KagikaiAPI = Field(exclude=True)

    def _run(self, **_kwargs: Any) -> str:
        return _j(self.api.get("/v1/instruments/available"))


class KagikaiRecycleInstrument(BaseTool):
    name: str = "kagikai_recycle_instrument"
    description: str = (
        "Recycle an available instrument: reset to Confirmed with new parameters."
    )
    args_schema: type[BaseModel] = RecycleInstrumentInput
    api: KagikaiAPI = Field(exclude=True)

    def _run(
        self,
        instrument_id: str,
        timeout_blocks: Optional[int] = None,
        evaluator_type: Optional[str] = None,
        evaluator_config: Optional[dict[str, Any]] = None,
        **_kwargs: Any,
    ) -> str:
        body: dict[str, Any] = {}
        if timeout_blocks is not None:
            body["timeout_blocks"] = timeout_blocks
        if evaluator_type is not None:
            body["evaluator_type"] = evaluator_type
        if evaluator_config is not None:
            body["evaluator_config"] = evaluator_config
        return _j(self.api.post(f"/v1/instrument/{instrument_id}/recycle", body))


class KagikaiRefundInstrument(BaseTool):
    name: str = "kagikai_refund_instrument"
    description: str = (
        "Refund an available instrument: sweep funds back to the creator's source address."
    )
    args_schema: type[BaseModel] = InstrumentIdInput
    api: KagikaiAPI = Field(exclude=True)

    def _run(self, instrument_id: str, **_kwargs: Any) -> str:
        return _j(self.api.post(f"/v1/instrument/{instrument_id}/refund", {}))


class KagikaiFeeEstimate(BaseTool):
    name: str = "kagikai_fee_estimate"
    description: str = (
        "Estimate fees for an escrow amount. Returns platform fee, mining fees, "
        "and net amount to recipient. No auth required."
    )
    args_schema: type[BaseModel] = AmountInput
    api: KagikaiAPI = Field(exclude=True)

    def _run(self, amount_sats: int, **_kwargs: Any) -> str:
        try:
            cfg = self.api.get("/admin/fee-config", auth=True)
            bps = cfg.get("fee_basis_points", 0)
            fee_min = cfg.get("fee_min_sats", 10)
            fee_max = cfg.get("fee_max_sats", 100000)
        except Exception:
            bps, fee_min, fee_max = 100, 10, 100000
        raw_fee = (amount_sats * bps) // 10000
        platform_fee = max(min(raw_fee, fee_max), fee_min) if bps > 0 else 0
        mining_total = 110 * 2 + 111 * 2  # forward + sweep
        return _j({
            "amount_sats": amount_sats,
            "platform_fee_sats": platform_fee,
            "mining_fee_total_sats": mining_total,
            "total_cost_sats": platform_fee + mining_total,
            "net_to_recipient_sats": amount_sats - platform_fee - mining_total,
        })


# ── Phase 14: Dispute tools ───────────────────────────────────────────


class KagikaiDisputeInstrument(BaseTool):
    name: str = "kagikai_dispute_instrument"
    description: str = (
        "Dispute an instrument in DisputeWindow status. Posts a bond to challenge delivery."
    )
    args_schema: type[BaseModel] = DisputeInstrumentInput
    api: KagikaiAPI = Field(exclude=True)

    def _run(self, instrument_id: str, reason: str, **_kwargs: Any) -> str:
        return _j(self.api.post("/v1/instrument/dispute", {
            "instrument_id": instrument_id,
            "reason": reason,
        }))


class KagikaiResolveDispute(BaseTool):
    name: str = "kagikai_resolve_dispute"
    description: str = (
        "Resolve a disputed instrument: uphold (buyer wins), reject (seller wins), "
        "or refund (seller voluntary)."
    )
    args_schema: type[BaseModel] = ResolveDisputeInput
    api: KagikaiAPI = Field(exclude=True)

    def _run(
        self,
        instrument_id: str,
        resolution: str,
        evidence: Optional[str] = None,
        **_kwargs: Any,
    ) -> str:
        body: dict[str, Any] = {
            "instrument_id": instrument_id,
            "resolution": resolution,
        }
        if evidence:
            body["evidence"] = evidence
        return _j(self.api.post("/v1/instrument/resolve", body))
