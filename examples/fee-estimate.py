"""
Fee estimation: check costs before creating an escrow.

The fee endpoint returns the platform fee (basis points), estimated
mining fees, and total cost breakdown. Use this to verify that
an escrow amount is viable before creating it.

Prerequisites:
    pip install httpx
    export KAGINET_API_KEY=kagi_your_api_key_here
"""

import os

import httpx

BASE = "https://mcp.kaginet.com"
API_KEY = os.environ["KAGINET_API_KEY"]
HEADERS = {"Authorization": f"Bearer {API_KEY}"}


def estimate_fee(amount_sats: int):
    """Get fee estimate for a given escrow amount."""
    with httpx.Client(timeout=15.0) as client:
        resp = client.get(
            f"{BASE}/v1/fee-estimate",
            params={"amount_sats": amount_sats},
            headers=HEADERS,
        )
        resp.raise_for_status()
        fee = resp.json()

    print(f"Fee estimate for {amount_sats:,} sats:")
    print(f"  Platform fee: {fee.get('platform_fee_sats', 'N/A')} sats "
          f"({fee.get('fee_basis_points', 'N/A')} bps)")
    print(f"  Forward mining fee: {fee.get('forward_fee_sats', 'N/A')} sats")
    print(f"  Sweep mining fee: {fee.get('sweep_fee_sats', 'N/A')} sats")
    print(f"  Total fees: {fee.get('total_fee_sats', 'N/A')} sats")
    print(f"  Payee receives: {fee.get('payee_receives_sats', 'N/A')} sats")
    print(f"  Viable: {fee.get('viable', 'N/A')}")

    if not fee.get("viable"):
        print(f"  Reason: {fee.get('reason', 'Amount too small to cover fees')}")

    return fee


def main():
    print("=== Fee estimates at different amounts ===\n")

    for amount in [2_000, 10_000, 50_000, 100_000, 1_000_000]:
        estimate_fee(amount)
        print()


if __name__ == "__main__":
    main()
