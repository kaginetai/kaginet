"""
TDX quote structural verification for Kagikai attestation documents.

Verifies the TDX quote returned by the TEE attestation sidecar:
- Parses the TDX quote binary structure
- Extracts REPORTDATA (64 bytes at offset 568)
- Compares the embedded code_hash against the attestation document's code_hash
- Validates quote header fields (version, attestation key type, TEE type)

This is structural verification, not full Intel DCAP chain verification.
Full DCAP requires Intel's Provisioning Certification Service (PCS) API
and is deferred to a future release.
"""

import base64
import struct
from dataclasses import dataclass
from typing import Optional, Tuple


# TDX quote v4 constants (Intel TDX Module 1.5 specification)
TDX_QUOTE_HEADER_SIZE = 48
TDX_REPORT_BODY_OFFSET = TDX_QUOTE_HEADER_SIZE
TDX_REPORT_BODY_SIZE = 584
TDX_REPORTDATA_OFFSET_IN_BODY = 520  # REPORTDATA is at offset 520 within TD Report Body
TDX_REPORTDATA_SIZE = 64

# Absolute offset of REPORTDATA in the full quote
TDX_REPORTDATA_OFFSET = TDX_REPORT_BODY_OFFSET + TDX_REPORTDATA_OFFSET_IN_BODY

# Header field offsets
HEADER_VERSION_OFFSET = 0        # u16 LE, expected 4
HEADER_ATT_KEY_TYPE_OFFSET = 2   # u16 LE, expected 2 (ECDSA-256-with-P-256)
HEADER_TEE_TYPE_OFFSET = 4       # u32 LE, expected 0x81 (TDX)
HEADER_VENDOR_ID_OFFSET = 12     # 16 bytes, Intel SGX vendor ID

INTEL_SGX_VENDOR_ID = bytes([
    0x93, 0x9A, 0x72, 0x33, 0xF7, 0x9C, 0x4C, 0xA9,
    0x94, 0x0A, 0x0D, 0xB3, 0x95, 0x7F, 0x06, 0x07,
])


@dataclass
class TdxQuoteInfo:
    """Parsed TDX quote metadata."""
    version: int
    att_key_type: int
    tee_type: int
    vendor_id: bytes
    report_data: bytes
    code_hash_from_report: str  # First 32 bytes of REPORTDATA as hex
    quote_size: int
    valid_header: bool
    valid_vendor: bool


@dataclass
class TdxVerificationResult:
    """Result of TDX quote structural verification."""
    valid: bool
    code_hash_match: bool
    quote_info: Optional[TdxQuoteInfo]
    error: Optional[str]


def parse_tdx_quote(quote_b64: str) -> Tuple[Optional[TdxQuoteInfo], Optional[str]]:
    """Parse a base64-encoded TDX quote and extract structural fields.

    Returns (TdxQuoteInfo, None) on success or (None, error_message) on failure.
    """
    try:
        quote_bytes = base64.b64decode(quote_b64)
    except Exception as e:
        return None, f"base64 decode failed: {e}"

    min_size = TDX_REPORTDATA_OFFSET + TDX_REPORTDATA_SIZE
    if len(quote_bytes) < min_size:
        return None, f"quote too short: {len(quote_bytes)} bytes, need at least {min_size}"

    # Parse header fields
    version = struct.unpack_from("<H", quote_bytes, HEADER_VERSION_OFFSET)[0]
    att_key_type = struct.unpack_from("<H", quote_bytes, HEADER_ATT_KEY_TYPE_OFFSET)[0]
    tee_type = struct.unpack_from("<I", quote_bytes, HEADER_TEE_TYPE_OFFSET)[0]
    vendor_id = quote_bytes[HEADER_VENDOR_ID_OFFSET:HEADER_VENDOR_ID_OFFSET + 16]

    # Extract REPORTDATA (64 bytes)
    report_data = quote_bytes[TDX_REPORTDATA_OFFSET:TDX_REPORTDATA_OFFSET + TDX_REPORTDATA_SIZE]

    # First 32 bytes of REPORTDATA contain the code_hash (zero-padded to 64 bytes)
    code_hash_from_report = report_data[:32].hex()

    valid_header = version == 4 and att_key_type == 2 and tee_type == 0x81
    valid_vendor = vendor_id == INTEL_SGX_VENDOR_ID

    info = TdxQuoteInfo(
        version=version,
        att_key_type=att_key_type,
        tee_type=tee_type,
        vendor_id=vendor_id,
        report_data=report_data,
        code_hash_from_report=code_hash_from_report,
        quote_size=len(quote_bytes),
        valid_header=valid_header,
        valid_vendor=valid_vendor,
    )

    return info, None


def verify_tdx_attestation(
    attestation: dict,
    expected_code_hash: Optional[str] = None,
) -> TdxVerificationResult:
    """Verify a Kagikai attestation document's TDX quote.

    Checks:
    1. Attestation mode is "tdx"
    2. tdx_quote_base64 field is present and non-empty
    3. Quote parses as a valid TDX v4 quote
    4. Quote header has correct version (4), key type (ECDSA-256), TEE type (TDX)
    5. Vendor ID matches Intel SGX
    6. REPORTDATA first 32 bytes match the attestation's code_hash
    7. If expected_code_hash provided, also matches that

    Args:
        attestation: The attestation document JSON (dict)
        expected_code_hash: Optional known-good code hash to verify against

    Returns:
        TdxVerificationResult with validation details
    """
    mode = attestation.get("mode", "")
    if mode != "tdx":
        return TdxVerificationResult(
            valid=False,
            code_hash_match=False,
            quote_info=None,
            error=f"attestation mode is '{mode}', expected 'tdx'",
        )

    quote_b64 = attestation.get("tdx_quote_base64", "")
    if not quote_b64:
        return TdxVerificationResult(
            valid=False,
            code_hash_match=False,
            quote_info=None,
            error="tdx_quote_base64 is missing or empty",
        )

    quote_info, parse_error = parse_tdx_quote(quote_b64)
    if parse_error:
        return TdxVerificationResult(
            valid=False,
            code_hash_match=False,
            quote_info=None,
            error=f"quote parse failed: {parse_error}",
        )

    if not quote_info.valid_header:
        return TdxVerificationResult(
            valid=False,
            code_hash_match=False,
            quote_info=quote_info,
            error=(
                f"invalid header: version={quote_info.version} (expect 4), "
                f"att_key_type={quote_info.att_key_type} (expect 2), "
                f"tee_type=0x{quote_info.tee_type:x} (expect 0x81)"
            ),
        )

    if not quote_info.valid_vendor:
        return TdxVerificationResult(
            valid=False,
            code_hash_match=False,
            quote_info=quote_info,
            error=f"vendor ID mismatch: got {quote_info.vendor_id.hex()}, expected Intel SGX",
        )

    # Compare REPORTDATA code_hash against attestation document code_hash
    attestation_code_hash = attestation.get("code_hash", "")
    code_hash_match = quote_info.code_hash_from_report == attestation_code_hash

    if not code_hash_match:
        return TdxVerificationResult(
            valid=False,
            code_hash_match=False,
            quote_info=quote_info,
            error=(
                f"code_hash mismatch: REPORTDATA contains {quote_info.code_hash_from_report}, "
                f"attestation says {attestation_code_hash}"
            ),
        )

    # Optionally check against a known-good code hash
    if expected_code_hash and quote_info.code_hash_from_report != expected_code_hash:
        return TdxVerificationResult(
            valid=False,
            code_hash_match=False,
            quote_info=quote_info,
            error=(
                f"code_hash does not match expected: REPORTDATA contains "
                f"{quote_info.code_hash_from_report}, expected {expected_code_hash}"
            ),
        )

    return TdxVerificationResult(
        valid=True,
        code_hash_match=True,
        quote_info=quote_info,
        error=None,
    )
