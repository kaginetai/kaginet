# TEE Attestation

Kaginet runs inside an Intel TDX (Trust Domain Extensions) enclave. This document explains how TDX attestation proves that the issuer key was deleted by audited code, and how to verify it independently.

## The Problem

In any escrow system, you need assurance that the escrow operator cannot steal funds. Traditional approaches:

- **Smart contracts**: code is public, verified by every node (transparent but public ledger)
- **Multi-signature**: requires multiple parties to collude (trust distributed but not eliminated)
- **Custodial**: trust the operator's reputation (no cryptographic guarantee)

Kaginet uses a fourth approach: **hardware attestation**. The keys exist only inside an Intel TDX enclave. The operator cannot read the enclave's memory. Intel's hardware produces a signed quote proving which code is running.

## Attestation Levels

| Level | Name | What it proves |
|-------|------|----------------|
| L0 | None | Software self-report only |
| L1 | Code attestation | The binary hash matches a known audit |
| L2 | Hardware isolation | Keys live in hardware-encrypted memory, host cannot read |
| L3 | Provable key deletion | Hardware proves the audited code ran AND the key was deleted |

Kaginet achieves L3 via Intel TDX.

## How It Works

### Key Lifecycle Inside the TEE

1. **Generate**: kA (issuer), kB (bearer), kC (creator) generated via CSPRNG inside TDX-encrypted memory
2. **Derive**: P2TR address computed from kB and kC via Taproot aggregate key, with CLTV recovery script using kA
3. **Delete**: kA is securely zeroed. This is the issuer lockout: the recovery script path requires kA, which no longer exists.
4. **Attest**: TDX hardware signs a quote containing the code hash of the running binary

### What the TDX Quote Contains

```
TDX Quote (approximately 5,010 bytes):
├── Header (48 bytes)
│   ├── Version: 4
│   ├── Attestation Key Type: ECDSA-256
│   └── TEE Type: 0x81 (TDX)
├── Body (584 bytes)
│   ├── MRTD: Hash of the entire VM image (measured at boot by hardware)
│   ├── REPORTDATA (64 bytes):
│   │   ├── Bytes 0-31: SHA-256 code hash of the ICS binary
│   │   └── Bytes 32-63: zeros (reserved)
│   └── Other measurement registers
├── Signature (64 bytes ECDSA)
└── Certificate Chain
    ├── Intel SGX PCK Certificate
    ├── Intermediate CA
    └── Intel Root CA
```

### What This Proves

| Claim | How |
|-------|-----|
| kA was generated inside the enclave | MRTD proves the audited binary is running. That binary generates kA via CSPRNG inside encrypted memory. |
| kA never left the enclave | TDX hardware encrypts all enclave memory pages. The host cannot read process memory. |
| kA was deleted | MRTD proves the running code is the code that zeros kA immediately after address derivation. |
| The deletion code was not tampered with | MRTD is computed by Intel TDX hardware before the VM boots. Any code modification changes MRTD. |
| The quote is genuine | Signed by Intel's attestation infrastructure, chain of trust to Intel root CA. |

## Verification

### Using the MCP tool

```
Use kagikai_verify_tdx_quote for instrument <uuid>
```

### Using the REST API

```bash
# Fetch the attestation
curl https://mcp.kaginet.com/v1/attestation/<instrument_id>
```

Response:
```json
{
  "instrument_id": "uuid",
  "mode": "tdx",
  "code_hash": "f51301...",
  "ka_deleted_at_ns": 1716505200000000000,
  "ka_generated_at_ns": 1716505199999000000,
  "tdx_quote_base64": "BAACAIEAAAA..."
}
```

### Using the Python verifier

```python
# pip install kagikai (or use verify/tdx_verify.py from this repo)
from kagikai.tdx_verify import verify_tdx_attestation

attestation = {
    "mode": "tdx",
    "code_hash": "f51301...",
    "tdx_quote_base64": "BAACAIEAAAA..."
}

result = verify_tdx_attestation(attestation)
print(f"Valid: {result.valid}")
print(f"Code hash match: {result.code_hash_match}")
print(f"Quote version: {result.quote_info.version}")
print(f"TEE type: {hex(result.quote_info.tee_type)}")
print(f"Quote size: {result.quote_info.quote_size} bytes")
```

### Manual Verification Steps

1. **Decode** the base64 `tdx_quote_base64` field
2. **Check header**: bytes 0-1 = version 4, bytes 4-5 = TEE type 0x81 (TDX)
3. **Extract REPORTDATA**: body offset, first 32 bytes
4. **Compare**: REPORTDATA code hash matches the `code_hash` field in the attestation
5. **Verify signature**: validate the ECDSA signature against the Intel SGX PCK certificate
6. **Validate certificate chain**: PCK cert → Intermediate CA → Intel Root CA

Steps 1-4 are structural verification (done by our verifier tool). Steps 5-6 are full Intel DCAP chain verification (requires Intel's verification service or the DCAP SDK).

## Timestamps

The attestation includes nanosecond-precision timestamps:

- `ka_generated_at_ns`: when kA was generated inside the TEE
- `ka_deleted_at_ns`: when kA was zeroed

The deletion happens within microseconds of generation (sub-millisecond). These timestamps are captured inside the TEE and included in the attestation document.

## Attestation Modes

| Mode | When | What |
|------|------|------|
| `tdx` | Running in a TDX-capable confidential VM | Full L3 attestation with Intel-signed quote |
| `local` | Development or non-TEE deployment | SHA-256 hash of the ICS binary (L1 only) |

The `/health` endpoint reports which attestation mode is active.
