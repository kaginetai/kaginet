# Security Model

## Trust Boundaries

Kaginet has three trust boundaries:

### 1. Bitcoin consensus (strongest)

The P2TR escrow address is enforced by every Bitcoin full node. No party, including Kaginet, can spend from the escrow without the correct keys. This is mathematical enforcement, not policy.

### 2. Intel TDX hardware (strong)

Private keys exist only inside the TDX enclave. The host operator cannot read enclave memory. Intel TDX hardware encrypts memory pages and provides attestation proving which code is running. The trust assumption is: Intel's TDX implementation is correct.

### 3. MCP/API authentication (standard)

Developer API keys (`kagi_*`) provide per-developer instrument isolation. This is standard bearer-token authentication. Compromised API keys can create instruments and submit evidence, but cannot extract private keys from the TEE.

## Threat Model

### Threats mitigated

| Threat | Mitigation |
|--------|-----------|
| **Operator steals funds** | Issuer key (kA) destroyed before funding, proven by TDX attestation. Operator has no spending path. |
| **Host reads private keys** | TDX encrypts enclave memory. Host cannot read process memory pages. |
| **Code tampered with** | MRTD (TDX measurement) changes if any code is modified. Attestation becomes invalid. |
| **Single Bitcoin node lies** | Dual-node verification: mempool.space + blockstream.info must agree. |
| **Payer freezes funds** | Timeout auto-expires instruments. CLTV recovery path available after timelock. |
| **Frivolous disputes** | Dispute bond (default 10%) creates economic cost for false disputes. |
| **Rapid vault drain** | Circuit breaker: per-creator daily limits on refund withdrawals. |
| **Approval timeout abuse** | Human approval instruments auto-expire after 72 hours. |
| **Rate limit bypass** | Per-developer sliding window rate limiter (60 calls/minute). |
| **Unauthorized instrument creation** | Per-developer API key auth with SHA-256 hashing. Keys revocable via dashboard. |

### Threats accepted (known limitations)

| Threat | Status |
|--------|--------|
| **Intel TDX compromise** | Kaginet's security depends on Intel TDX correctness. A fundamental TDX bypass would affect all TEE-based systems. |
| **Bitcoin 51% attack** | Standard Bitcoin assumption. Affects all Bitcoin-based systems equally. |
| **Server availability** | Single server instance. Server downtime prevents new instrument creation and sweeps. Existing on-chain instruments remain safe (keys in encrypted WAL). |
| **API key compromise** | Compromised key can create instruments charged to the developer. Cannot extract TEE keys. Revoke keys at cloud.kaginet.com. |
| **Network partitioning** | If both Bitcoin explorer nodes are unreachable, the watcher pauses. Instruments remain safe on-chain. |

## Key Management

### Key types and lifecycles

| Key | Algorithm | Generated | Stored | Destroyed |
|-----|-----------|-----------|--------|-----------|
| kA (issuer) | secp256k1 | Inside TEE | Never stored (zeroed immediately) | Before funding |
| kB (bearer) | secp256k1 | Inside TEE | TEE memory + encrypted WAL | After sweep/refund tx broadcast |
| kC (creator) | secp256k1 | Inside TEE | TEE memory + encrypted WAL | After sweep/refund tx broadcast |
| kF (forward) | secp256k1 | Inside TEE | TEE memory + encrypted WAL | After forward tx confirms |

### Zeroization

All private keys are zeroed using secure memory operations. After zeroization:
- The key bytes are overwritten with zeros
- The instrument transitions to a terminal state (Swept or Refunded)
- The instrument is excluded from WAL persistence

### Encrypted persistence

Non-terminal instruments persist across server restarts via an encrypted write-ahead log. Terminal instruments (Swept, Refunded) have their keys zeroed and are excluded from persistence. The WAL is crash-safe: writes are atomic and encrypted at rest.

## Authentication

### Developer API keys

- Format: `kagi_` prefix + 64 hex characters
- Storage: SHA-256 hash stored in Postgres (plaintext never persisted)
- Per-developer isolation: each developer's instruments are scoped by `creator_id` in the JWT
- Maximum 10 keys per developer
- Revocable via dashboard

### ICS authentication

- Ed25519 JWT tokens signed by the MCP server
- 60-second expiry per request
- Claims: `sub` (developer_id), `iss` (kaginet-dashboard), `aud` (kagikai-ics)

### Rate limiting

- MCP tools: 60 calls per minute per developer (sliding window)
- Dashboard API: 5 registrations per minute per IP, 10 logins per minute per IP

## Circuit Breaker

Vault refund operations have a per-creator circuit breaker:

| Control | Default | Purpose |
|---------|---------|---------|
| Max single refund | 1,000,000 sats | Prevents single large unauthorized withdrawal |
| Max daily total | 5,000,000 sats | Rolling window cap on total refund volume |
| Cooldown | 3,600 seconds | Mandatory wait after a large refund |

## Responsible Disclosure

See [SECURITY.md](../SECURITY.md) for reporting vulnerabilities.
