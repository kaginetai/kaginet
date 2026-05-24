---
name: kaginet-escrow
description: Create and manage Bitcoin escrow payments between AI agents using Kaginet. Hardware-attested key lifecycle inside Intel TDX enclaves. Supports hash-match, human approval, and optimistic settlement with dispute bonds.
version: 1.0.0
metadata:
  hermes:
    tags: [bitcoin, payment, escrow, mcp, agent-commerce]
    category: finance
    requires_tools: [mcp]
    config:
      - key: kaginet.api_key
        description: "Kaginet API key from cloud.kaginet.com (kagi_* prefix)"
        prompt: "Enter your Kaginet API key"
      - key: kaginet.mcp_url
        description: "Kaginet MCP endpoint URL"
        default: "https://mcp.kaginet.com/sse"
---

# Kaginet Bitcoin Escrow

## When to Use

Use this skill when:
- An agent needs to pay another agent for completed work
- You need conditional payment release (pay only if the work matches expectations)
- You need escrow with hash-match verification, human approval, or optimistic settlement
- You want hardware-attested proof that payment keys were generated and deleted securely
- You need Bitcoin-native settlement without custodians or intermediaries

Do NOT use this skill for:
- Fiat currency payments (use Stripe or Natural instead)
- Payments under 2,000 sats (below dust threshold)
- Recurring subscriptions (not yet supported)

## Prerequisites

1. **API Key**: Sign up at https://cloud.kaginet.com and create an API key
2. **MCP Server**: Add Kaginet as an MCP server in your config

## Setup

Add this to your MCP configuration:

```json
{
  "mcpServers": {
    "kaginet": {
      "url": "https://mcp.kaginet.com/sse",
      "headers": {
        "Authorization": "Bearer kagi_YOUR_API_KEY"
      }
    }
  }
}
```

For Hermes, set the config value:
```
hermes config set kaginet.api_key kagi_YOUR_API_KEY
```

## Procedure

### Creating an Escrow Payment

1. **Estimate fees first**
   Call `kaginet_fee_estimate` with the amount in sats to see total cost including platform fee (0.5%) and current mining fee estimate.

2. **Generate agent identity** (first time only)
   Call `kaginet_generate_identity` to create an X25519 keypair. This is your persistent payment identity. Save the public key.

3. **Create the escrow instrument**
   Call `kaginet_create_escrow` with:
   - `payee_address`: Bitcoin address of the recipient (bc1q... or bc1p...)
   - `amount_sats`: Amount in satoshis (minimum 2,000)
   - `description`: What the payment is for
   - `evaluator_type`: One of `hash_match`, `human_approval`, or `optimistic`
   - For `hash_match`: include `expected_hash` (SHA-256 hex of expected deliverable)
   - For `optimistic`: include `dispute_window_blocks` (default 6)

4. **Fund the escrow**
   The create response includes a `funding_address` (Taproot bc1p... address). Send the exact `funding_amount_sats` to this address. The system monitors for on-chain confirmation.

5. **Wait for funding confirmation**
   Call `kaginet_instrument_status` to check. Status progresses: `created` -> `funded` -> `submitted` -> `settled`.

6. **Submit evidence** (payee side)
   The payee calls `kaginet_submit_evidence` with the deliverable. For hash_match, the SHA-256 of the submission is compared to `expected_hash`.

7. **Settlement**
   On successful evaluation, funds are automatically swept to the payee's address. Call `kaginet_instrument_status` to confirm `settled` status.

### Disputing an Optimistic Escrow

1. Call `kaginet_dispute_escrow` with the escrow ID and reason during the dispute window
2. A bond instrument is created: fund it to activate the dispute
3. The evaluator resolves: dispute upheld (buyer gets refund + bond back) or rejected (seller gets payment, bond forfeited)

### Checking Attestation

Call `kaginet_get_attestation` to retrieve the Intel TDX quote proving the payment server runs inside a hardware enclave. Verify with:

```bash
python scripts/verify-attestation.py --url https://mcp.kaginet.com
```

## Available MCP Tools

| Tool | Purpose |
|------|---------|
| `kaginet_create_escrow` | Create a new escrow instrument |
| `kaginet_instrument_status` | Check instrument state |
| `kaginet_list_instruments` | List your instruments |
| `kaginet_submit_evidence` | Submit work for evaluation |
| `kaginet_dispute_escrow` | Dispute an optimistic escrow |
| `kaginet_fee_estimate` | Estimate total payment cost |
| `kaginet_generate_identity` | Create X25519 agent identity |
| `kaginet_get_agent` | Get agent profile and reputation |
| `kaginet_get_attestation` | Get TDX hardware attestation |
| `kaginet_verify_attestation` | Verify attestation quote |
| `kaginet_get_destinations` | List available payee addresses |
| `kaginet_create_destination` | Register a payee address |

## Fee Model

- **Platform fee**: 0.5% (50 basis points) of escrow amount
- **Mining fee**: Dynamic, based on current mempool (typically 1,000-5,000 sats)
- **Minimum escrow**: 2,000 sats
- **No fee on refund**: If escrow expires or is refunded, only the mining fee applies

## Pitfalls

- **Minimum amount**: Escrows below 2,000 sats will fail (Bitcoin dust limit)
- **Funding must be exact**: Send exactly the `funding_amount_sats` shown. Under-funding leaves the escrow unfunded. Over-funding is absorbed as mining fee.
- **Hash match is case-sensitive**: The SHA-256 hash must be lowercase hex
- **Dispute window is in blocks**: Not time. At ~10 min/block, 6 blocks is roughly 1 hour.
- **Keys are ephemeral**: The issuer key (kA) is deleted immediately after address derivation. This is a security feature, not a bug. It means the escrow cannot be modified after creation.
- **Rate limit**: 60 requests per minute per API key
- **Circuit breaker**: 50M sats daily global cap, 50 unfunded instruments per developer

## Verification

After creating an escrow, verify success by:
1. `kaginet_instrument_status` returns status `created` with a `funding_address`
2. The funding address starts with `bc1p` (Taproot)
3. `kaginet_get_attestation` returns a valid TDX quote (5,010 bytes, Quote v4)

## Links

- Dashboard: https://cloud.kaginet.com
- Docs: https://kaginet.com
- MCP endpoint: https://mcp.kaginet.com/sse
- A2A Agent Card: https://mcp.kaginet.com/.well-known/agent-card.json
- A2P Payment Protocol: https://kaginet.com/docs/a2p-protocol
