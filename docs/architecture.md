# Architecture

## System Overview

Kaginet is a hosted Bitcoin escrow service for AI agent payments. The core service runs inside an Intel TDX confidential VM (Trusted Execution Environment). Agents interact via MCP tools, framework adapters, or the REST API.

```
┌─────────────────────────────────────────────────────────────┐
│                    Agent Runtimes                           │
│  Claude Desktop │ GPT-4 │ Cursor │ CrewAI │ LangChain      │
└────────┬──────────────┬──────────────┬──────────────────────┘
         │              │              │
    MCP (SSE)     LangChain SDK    CrewAI SDK
         │              │              │
         ▼              ▼              ▼
┌─────────────────────────────────────────────────────────────┐
│                   MCP Server (SSE)                          │
│            mcp.kaginet.com:443/sse                          │
│                                                             │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │ Bearer Auth  │  │  Rate Limiter │  │ Ed25519 JWT Sign  │  │
│  │ kagi_* keys  │  │  60/min/dev   │  │ per-request       │  │
│  └─────────────┘  └──────────────┘  └───────────────────┘  │
└────────────────────────────┬────────────────────────────────┘
                             │ HTTPS + Ed25519 JWT
                             ▼
┌─────────────────────────────────────────────────────────────┐
│              ICS — Instrument Creation Service              │
│              (Intel TDX Confidential VM)                    │
│                                                             │
│   Key generation · State machine · UTXO monitoring          │
│   Transaction building · Evidence evaluation                │
│   TDX attestation · Encrypted persistence                   │
│                                                             │
│   All private keys and signing happen inside this boundary. │
│   Host operator cannot read enclave memory.                 │
└────────────────────────────┬────────────────────────────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
        ┌──────────┐  ┌──────────┐  ┌──────────┐
        │ Bitcoin   │  │ Bitcoin   │  │  Nostr   │
        │ Node 1    │  │ Node 2    │  │  Relays  │
        │mempool.   │  │blockstream│  │          │
        │  space    │  │  .info    │  │          │
        └──────────┘  └──────────┘  └──────────┘
```

## Trust Boundaries

### Inside the TEE (trusted)

Everything inside the Intel TDX enclave is hardware-isolated from the host operator:

- **Key generation**: secp256k1 keypairs (kA, kB, kC) generated via OS CSPRNG inside encrypted memory
- **Key deletion**: Issuer key (kA) zeroed immediately after P2TR address derivation
- **Key storage**: Bearer keys (kB, kC) exist only in TDX-encrypted memory until sealed or zeroed
- **Transaction signing**: Taproot key-path signing for sweeps and refunds
- **State machine**: All instrument status transitions and validation logic

The host operator cannot read the enclave's memory. This is enforced by Intel TDX hardware, not by policy.

### Outside the TEE (untrusted)

- **Bitcoin network**: Settlement layer. Transactions are broadcast and confirmed by Bitcoin consensus.
- **Blockchain explorers**: UTXO queries use dual-node verification (mempool.space + blockstream.info). Neither node is trusted individually.
- **Nostr relays**: Receipt notifications. Relays are untrusted message brokers.
- **MCP server**: Authentication and rate limiting layer. Does not handle keys or signing.

### Developer boundary

- **Dashboard**: cloud.kaginet.com provides API key management, escrow monitoring, and usage stats
- **Logto OIDC**: Authentication via standard OIDC flow
- **API keys**: `kagi_*` prefixed, SHA-256 hashed at rest, per-developer instrument isolation

## Data Flow: Escrow Lifecycle

### 1. Creation

```
Agent ──▶ kagikai_escrow_create(amount, payee_address)
          │
          ▼
MCP ────▶ POST /v1/instrument/create (no agent_x25519_pubkey = ICS-native)
          │
          ▼
ICS ────▶ Generate kA, kB, kC (inside TEE)
          Compute P2TR address from (kB, kC) Taproot aggregate + CLTV script
          Zero kA (issuer lockout)
          Generate bc1q forwarding address from kF
          │
          ▼
MCP ────▶ POST /v1/instrument/set-destination(payee_address)
          │
          ▼
Agent ◀── { instrument_id, funding_address (bc1q), payment_uri (BIP-21) }
```

### 2. Funding + Auto-Forward

```
Payer ──▶ Send bitcoin to bc1q funding address (any wallet)
          │
          ▼
ICS ────▶ Watcher detects bc1q UTXO
          Build P2WPKH→P2TR forward transaction
          Sign with kF (ECDSA)
          Broadcast to Bitcoin network
          Status: WatchingForFunding → Forwarding
          │
          ▼
Bitcoin ─▶ Forward tx confirms
          Status: Forwarding → Confirmed
```

### 3. Release + Auto-Sweep

```
Agent ──▶ kagikai_escrow_release(instrument_id, evidence)
          │
          ▼
ICS ────▶ Evaluate evidence (hash_match / human_approval / optimistic)
          Status: Confirmed → Submitted → Completed
          │
          ▼
ICS ────▶ Watcher: Completed + destination set
          Build P2TR key-path sweep transaction
          Sign with Taproot key-path spend (kB, kC)
          Broadcast to Bitcoin network
          Zero kB, kC (keys destroyed)
          Status: Completed → Swept (terminal)
          │
          ▼
Payee ◀── Bitcoin received at destination address
```

## Key Types

| Key | Name | Purpose | Lifecycle |
|-----|------|---------|-----------|
| kA | Issuer key | Recovery script path (with CLTV timelock) | Destroyed before funding. TDX attestation proves deletion. |
| kB | Bearer key | Taproot key-path participant | Held in TEE. Used for sweep/refund signing. Zeroed after sweep. |
| kC | Creator key | Taproot key-path participant | Held in TEE. Used for sweep/refund signing. Zeroed after sweep. |
| kF | Forwarding key | P2WPKH signing for bc1q→bc1p forward | Generated for ICS-native mode. Zeroed after forward confirms. |

## Evaluator Types

| Type | Behavior |
|------|----------|
| `hash_match` | Auto-approve if SHA-256 of evidence matches pre-agreed hash |
| `human_approval` | Wait for manual complete/reject call (72h timeout) |
| `optimistic` | Auto-approve after dispute window (default 3 days). Buyer can dispute with bond. |

## Dual-Node Verification

All UTXO queries use two independent Bitcoin explorers:

1. Try node 1 (mempool.space)
2. If node 1 fails (rate limit, timeout, error), fall back to node 2 (blockstream.info)
3. Only skip the poll cycle if BOTH nodes are unreachable

This prevents rate-limited responses from being silently treated as "no UTXOs found."

## Persistence

Non-terminal instruments persist across server restarts via an encrypted write-ahead log (WAL). Terminal instruments (Swept, Refunded) have their keys zeroed and are excluded from persistence.
