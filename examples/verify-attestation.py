"""
Verify a TDX attestation for any Kaginet instrument.

Fetches the attestation document from the ICS and runs structural
verification on the TDX quote: header fields, Intel vendor ID,
and REPORTDATA code_hash match.

Prerequisites:
    pip install httpx
"""

import sys
import os

import httpx

# Add the repo root to path so we can import the verify module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from verify.tdx_verify import verify_tdx_attestation

BASE_URL = "https://mcp.kaginet.com"


def verify(instrument_id: str, expected_code_hash: str | None = None):
    """Fetch and verify a TDX attestation for an instrument."""
    print(f"Fetching attestation for {instrument_id}...")

    with httpx.Client(timeout=15.0) as client:
        # Attestation endpoint is public (no auth required)
        resp = client.get(f"{BASE_URL}/v1/attestation/{instrument_id}")
        resp.raise_for_status()
        attestation = resp.json()

    print(f"  Mode: {attestation.get('mode')}")
    print(f"  Code hash: {attestation.get('code_hash', 'N/A')}")

    if attestation.get("tdx_quote_base64"):
        quote_len = len(attestation["tdx_quote_base64"])
        print(f"  TDX quote: {quote_len} chars (base64)")
    else:
        print("  TDX quote: not present")

    # Run structural verification
    result = verify_tdx_attestation(attestation, expected_code_hash=expected_code_hash)

    print()
    if result.valid:
        print("PASS: TDX attestation valid")
        info = result.quote_info
        print(f"  Quote version: {info.version}")
        print(f"  TEE type: 0x{info.tee_type:x}")
        print(f"  Quote size: {info.quote_size} bytes")
        print(f"  Code hash in REPORTDATA: {info.code_hash_from_report}")
        print(f"  Code hash match: {result.code_hash_match}")
    else:
        print(f"FAIL: TDX attestation invalid: {result.error}")

    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python verify-attestation.py <instrument_id> [expected_code_hash]")
        print()
        print("Example:")
        print("  python verify-attestation.py abc123-def456-ghi789")
        print("  python verify-attestation.py abc123-def456-ghi789 367e6cb9...")
        sys.exit(1)

    iid = sys.argv[1]
    code_hash = sys.argv[2] if len(sys.argv) > 2 else None
    verify(iid, code_hash)
