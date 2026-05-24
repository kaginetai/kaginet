# API Reference

Base URL: `https://mcp.kaginet.com` (or your self-hosted ICS instance)

## Authentication

All authenticated endpoints require a Bearer token:

```
Authorization: Bearer kagi_YOUR_API_KEY
```

API keys are created at [cloud.kaginet.com](https://cloud.kaginet.com) under Keys. Keys are prefixed with `kagi_` and shown only once on creation.

The MCP server signs per-request Ed25519 JWTs for ICS calls, providing per-developer instrument isolation.

---

## Health

### GET /health

Check service health, network, and node connectivity. No authentication required.

```bash
curl https://mcp.kaginet.com/health
```

**Response:**
```json
{
  "status": "ok",
  "version": "1.4.0",
  "network": "mainnet",
  "api_version": "1.0",
  "node1_reachable": true,
  "node2_reachable": true,
  "relay_count": 3,
  "attestation_mode": "tdx"
}
```

---

## Instruments

### POST /v1/instrument/create

Create a new instrument (escrow).

**Request:**
```json
{
  "amount_sats": 50000,
  "agent_x25519_pubkey": "64-char hex (optional, omit for ICS-native)",
  "job_id": "optional-job-id",
  "locktime_blocks": 4320,
  "timeout_blocks": 144,
  "evaluator_type": "hash_match",
  "evaluator_config": {
    "expected_hash": "sha256-hex-of-expected-deliverable"
  }
}
```

- Omit `agent_x25519_pubkey` for ICS-native mode (recommended for escrows). ICS retains keys and handles sweep automatically.
- Include `agent_x25519_pubkey` for legacy mode where keys are sealed to the agent.

**Response:**
```json
{
  "instrument_id": "uuid",
  "p2tr_address": "bc1p...",
  "funding_address": "bc1q... (ICS-native only)",
  "ics_native": true,
  "fee_sats": 250,
  "estimated_mining_fee_sats": 442,
  "fee_rate_sat_vb": 2,
  "estimated_net_sats": 49308,
  "sealed_payload_b64": "... (legacy mode only)",
  "attestation": {
    "mode": "tdx",
    "code_hash": "hex...",
    "ka_deleted_at_ns": 1716505200000000000,
    "ka_generated_at_ns": 1716505199999000000
  }
}
```

### POST /v1/instrument/confirm

Confirm an instrument after funding (legacy mode). Verifies UTXO exists with correct amount and fee output.

**Request:**
```json
{
  "instrument_id": "uuid",
  "txid": "64-char hex bitcoin txid"
}
```

### GET /v1/instrument/{id}/status

Get current instrument status.

**Response:**
```json
{
  "instrument_id": "uuid",
  "status": "confirmed",
  "amount_sats": 50000,
  "fee_sats": 250,
  "p2tr_address": "bc1p...",
  "funding_address": "bc1q...",
  "forward_txid": "hex...",
  "sweep_destination": "bc1q...payee",
  "sweep_txid": null,
  "refund_txid": null,
  "creator_source_address": "bc1q...funder",
  "evaluator_type": "hash_match",
  "evidence": null,
  "reject_reason": null,
  "created_at": "2026-05-24T01:00:00Z",
  "confirmed_at": "2026-05-24T01:05:00Z",
  "submitted_at": null,
  "completed_at": null,
  "deadline_block_height": 900144,
  "ics_native": true,
  "dispute_window_opened_at": null,
  "dispute_window_blocks": null,
  "bond_instrument_id": null,
  "bond_amount_sats": null,
  "dispute_reason": null,
  "disputed_at": null
}
```

### POST /v1/instrument/submit

Submit evidence for evaluation.

**Request:**
```json
{
  "instrument_id": "uuid",
  "evidence": "https://example.com/deliverable or sha256-hash"
}
```

### POST /v1/instrument/complete

Manually approve a submitted instrument (human_approval evaluator).

**Request:**
```json
{
  "instrument_id": "uuid"
}
```

### POST /v1/instrument/reject

Reject a submitted instrument.

**Request:**
```json
{
  "instrument_id": "uuid",
  "reason": "Deliverable does not match requirements"
}
```

### POST /v1/instrument/set-destination

Set or change the sweep destination for an ICS-native instrument.

**Request:**
```json
{
  "instrument_id": "uuid",
  "destination_address": "bc1q...payee-address"
}
```

---

## Batch Operations

### POST /v1/batch/create

Create multiple instruments in a single call. One TDX attestation covers the entire batch. Maximum 20 instruments per batch.

**Request:**
```json
{
  "instruments": [
    {"amount_sats": 10000, "label": "milestone-1"},
    {"amount_sats": 20000, "label": "milestone-2"},
    {"amount_sats": 20000, "label": "milestone-3"}
  ],
  "agent_x25519_pubkey": "64-char hex (optional)",
  "job_id": "project-123"
}
```

### GET /v1/batch/{batch_id}/status

Get status of all instruments in a batch.

---

## Vault (Available Instruments)

### GET /v1/instruments/available

List instruments in Available status (expired or rejected, funds still on-chain). Scoped to the authenticated creator.

### POST /v1/instrument/{id}/recycle

Recycle an Available instrument: reset to Confirmed with new parameters. No on-chain transaction.

**Request:**
```json
{
  "timeout_blocks": 288,
  "evaluator_type": "hash_match",
  "evaluator_config": {"expected_hash": "..."}
}
```

### POST /v1/instrument/{id}/refund

Refund an Available instrument to the creator's original funding source address.

---

## Dispute

### POST /v1/instrument/dispute

Dispute an instrument in DisputeWindow status. Creates a bond instrument.

**Request:**
```json
{
  "instrument_id": "uuid",
  "reason": "Deliverable does not match the agreed specification"
}
```

**Response:**
```json
{
  "status": "disputed",
  "bond_instrument_id": "uuid-of-bond",
  "bond_amount_sats": 5000,
  "bond_funding_address": "bc1q..."
}
```

### POST /v1/instrument/resolve

Resolve a disputed instrument.

**Request:**
```json
{
  "instrument_id": "uuid",
  "resolution": "uphold",
  "evidence": "Optional resolution reasoning"
}
```

Resolution values: `uphold` (buyer wins), `reject` (seller wins), `refund` (seller voluntary refund).

---

## Verification

### POST /v1/verify

Verify a Bitcoin address has sufficient funds using dual-node verification.

**Request:**
```json
{
  "address": "bc1p...",
  "expected_sats": 50000
}
```

### GET /v1/attestation/{instrument_id}

Get the attestation document for an instrument. No authentication required.

**Response:**
```json
{
  "instrument_id": "uuid",
  "mode": "tdx",
  "code_hash": "hex...",
  "ka_deleted_at_ns": 1716505200000000000,
  "ka_generated_at_ns": 1716505199999000000,
  "tdx_quote_base64": "base64-encoded TDX quote (5010 bytes)"
}
```

---

## Agent Identity

### GET /v1/agent/{pubkey_hex}

Get agent identity and profile. No authentication required.

### PUT /v1/agent/{pubkey_hex}

Update agent profile (display name, capabilities, URL). Authenticated.

### GET /v1/agent/{pubkey_hex}/agent.json

Get a Google A2A-compatible Agent Card. No authentication required.

### GET /v1/reputation/{pubkey_hex}

Get reputation stats (created, received, transferred, disputed, completed ratio). No authentication required.

---

## Nostr Receipt Watch

### POST /v1/receipt/watch

Start watching Nostr relays for a transfer receipt. Expires after 600 seconds.

### DELETE /v1/receipt/watch/{watch_id}

Cancel an active receipt watch.

---

## Admin

### GET /admin/fee-config

Get current fee configuration. Authenticated.

**Response:**
```json
{
  "fee_basis_points": 50,
  "fee_min_sats": 10,
  "fee_max_sats": 100000,
  "fee_priority": "economy",
  "forward_fee_rate_sat_vb": 2,
  "sweep_fee_rate_sat_vb": 2,
  "min_fee_rate_sat_vb": 1,
  "max_fee_rate_sat_vb": 50,
  "fee_address": "bc1q..."
}
```

---

## Error Responses

All error responses follow the format:

```json
{
  "error": "Human-readable error message"
}
```

Common HTTP status codes:
- `400` — Invalid request (bad parameters, invalid state transition)
- `401` — Missing or invalid authentication
- `403` — Forbidden (not the instrument creator)
- `404` — Instrument not found
- `409` — Conflict (invalid state transition, e.g., confirming an already-confirmed instrument)
- `429` — Rate limited
- `503` — Service unavailable (both Bitcoin nodes unreachable)
