# MCP Tools

Kaginet exposes 29 MCP tools via the SSE endpoint at `mcp.kaginet.com/sse`. Any MCP-compatible agent runtime (Claude Desktop, Cursor, Windsurf, GPT-4 with MCP support) can use these tools.

## Configuration

```json
{
  "mcpServers": {
    "kagikai": {
      "url": "https://mcp.kaginet.com/sse",
      "headers": {
        "Authorization": "Bearer kagi_YOUR_API_KEY"
      }
    }
  }
}
```

## Tool Categories

### Escrow (recommended for most use cases)

These are the high-level tools for creating and managing escrows. They handle the ICS-native instrument lifecycle automatically.

#### kagikai_escrow_create

Create a new escrow with auto-sweep. Returns a bc1q funding address and BIP-21 payment URI.

```json
{
  "amount_sats": 50000,
  "payee_address": "bc1q...recipient",
  "description": "Payment for logo design",
  "timeout_blocks": 144,
  "evaluator_type": "hash_match",
  "evaluator_config": {"expected_hash": "sha256hex..."}
}
```

Required: `amount_sats`, `payee_address`

#### kagikai_escrow_status

Check escrow status, funding/forwarding/sweep transaction IDs.

```json
{"instrument_id": "uuid"}
```

#### kagikai_escrow_release

Release escrow: submit evidence to trigger evaluation and auto-sweep.

```json
{
  "instrument_id": "uuid",
  "evidence": "https://example.com/deliverable"
}
```

#### kagikai_escrow_cancel

Cancel/reject an escrow.

```json
{
  "instrument_id": "uuid",
  "reason": "Deliverable not received"
}
```

#### kagikai_set_destination

Set or change the sweep destination address.

```json
{
  "instrument_id": "uuid",
  "destination_address": "bc1q...new-payee"
}
```

#### kagikai_fee_estimate

Estimate fees for an escrow amount. No state change. Returns platform fee, mining fees, net amount.

```json
{"amount_sats": 50000}
```

---

### Vault and Recovery

Manage expired or rejected instruments whose funds are still on-chain.

#### kagikai_list_available

List Available instruments for the authenticated creator. No arguments.

#### kagikai_recycle_instrument

Reuse an expired/rejected instrument with new parameters. No on-chain transaction needed.

```json
{
  "instrument_id": "uuid",
  "timeout_blocks": 288,
  "evaluator_type": "hash_match",
  "evaluator_config": {"expected_hash": "..."}
}
```

#### kagikai_refund_instrument

Sweep funds back to the creator's original funding source address.

```json
{"instrument_id": "uuid"}
```

---

### Dispute (Optimistic Settlement)

For instruments using the `optimistic` evaluator type.

#### kagikai_dispute_instrument

Post a bond and dispute an instrument in DisputeWindow status.

```json
{
  "instrument_id": "uuid",
  "reason": "Deliverable does not match specification"
}
```

#### kagikai_resolve_dispute

Resolve a disputed instrument. Resolutions: `uphold` (buyer wins), `reject` (seller wins), `refund` (voluntary).

```json
{
  "instrument_id": "uuid",
  "resolution": "uphold",
  "evidence": "Reasoning for resolution"
}
```

---

### Instruments (Advanced)

Low-level instrument management. Use the escrow tools above for most use cases.

#### kagikai_create_instrument

Create a raw P2TR instrument. Include `agent_x25519_pubkey` for legacy sealed-key mode, omit for ICS-native.

```json
{
  "amount_sats": 50000,
  "agent_x25519_pubkey": "64-char hex",
  "job_id": "optional-id",
  "locktime_blocks": 4320
}
```

#### kagikai_confirm_instrument

Confirm an instrument after manual funding (legacy mode).

```json
{
  "instrument_id": "uuid",
  "txid": "64-char hex bitcoin txid"
}
```

#### kagikai_get_status

Get instrument status with all fields.

```json
{"instrument_id": "uuid"}
```

#### kagikai_submit_instrument

Submit evidence for evaluation.

```json
{
  "instrument_id": "uuid",
  "evidence": "https://example.com/deliverable"
}
```

#### kagikai_complete_instrument

Manually approve a submitted instrument.

```json
{"instrument_id": "uuid"}
```

#### kagikai_reject_instrument

Reject a submitted instrument.

```json
{
  "instrument_id": "uuid",
  "reason": "Does not meet requirements"
}
```

#### kagikai_batch_create

Batch create up to 20 instruments.

```json
{
  "instruments": [
    {"amount_sats": 10000, "label": "part-1"},
    {"amount_sats": 20000, "label": "part-2"}
  ],
  "agent_x25519_pubkey": "64-char hex",
  "job_id": "project-123"
}
```

#### kagikai_batch_status

Get status of all instruments in a batch.

```json
{"batch_id": "uuid"}
```

---

### Verification and Identity

#### kagikai_health

Check server health, network, and node connectivity. No authentication required.

#### kagikai_verify_address

Dual-node UTXO verification for a Bitcoin address.

```json
{
  "address": "bc1p...",
  "expected_sats": 50000
}
```

#### kagikai_get_attestation

Get the TDX attestation document for an instrument. No authentication required.

```json
{"instrument_id": "uuid"}
```

#### kagikai_verify_tdx_quote

Structurally verify the TDX quote in an attestation document. Checks quote header, Intel vendor ID, and REPORTDATA code_hash.

```json
{
  "instrument_id": "uuid",
  "expected_code_hash": "optional-known-good-hash"
}
```

#### kagikai_get_agent

Get agent identity and reputation summary.

```json
{"pubkey_hex": "64-char hex"}
```

#### kagikai_update_agent

Update agent profile (display name, capabilities, URL).

```json
{
  "pubkey_hex": "64-char hex",
  "display_name": "Payment Bot",
  "capabilities": ["payment", "escrow"],
  "url": "https://my-agent.example.com"
}
```

#### kagikai_get_agent_card

Get a Google A2A-compatible Agent Card.

```json
{"pubkey_hex": "64-char hex"}
```

#### kagikai_get_reputation

Get reputation stats for an agent.

```json
{"pubkey_hex": "64-char hex"}
```

#### kagikai_watch_receipt

Start watching Nostr relays for a transfer receipt. Watch expires after 600 seconds.

```json
{
  "instrument_id": "uuid",
  "nonce_hex": "64-char hex",
  "kb_pubkey_hex": "64-char hex",
  "webhook_url": "https://my-service.example.com/webhook"
}
```

#### kagikai_delete_watch

Cancel an active receipt watch.

```json
{"watch_id": "uuid"}
```

---

## Resource Templates

The MCP server also exposes two resource templates:

- `kagikai://instrument/{instrument_id}` — Full instrument state
- `kagikai://attestation/{instrument_id}` — Hardware attestation document
