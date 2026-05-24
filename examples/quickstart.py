"""
Quickstart: Create your first Kaginet escrow.

This example creates an escrow instrument, prints the funding address,
and polls until the status changes.

Prerequisites:
    pip install httpx
    export KAGINET_API_KEY=kagi_your_api_key_here
"""

import os
import time

import httpx

BASE = "https://mcp.kaginet.com"
API_KEY = os.environ["KAGINET_API_KEY"]
HEADERS = {"Authorization": f"Bearer {API_KEY}"}


def create_escrow():
    """Create a 10,000 sat escrow with hash_match evaluator."""
    with httpx.Client(timeout=30.0) as client:
        # Step 1: Create the escrow
        resp = client.post(
            f"{BASE}/v1/escrow",
            json={
                "amount_sats": 10_000,
                "payee_address": "bc1qexamplerecipientaddresshere",
                "description": "Quickstart test escrow",
                "evaluator_type": "hash_match",
                "evidence_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            },
            headers=HEADERS,
        )
        resp.raise_for_status()
        escrow = resp.json()

        instrument_id = escrow["instrument_id"]
        funding_address = escrow["funding_address"]
        amount = escrow["amount_sats"]

        print(f"Escrow created: {instrument_id}")
        print(f"Fund {amount} sats to: {funding_address}")
        print()

        # Step 2: Poll for status changes
        print("Waiting for funding (Ctrl+C to stop)...")
        while True:
            status_resp = client.get(
                f"{BASE}/v1/instruments/{instrument_id}",
                headers=HEADERS,
            )
            status = status_resp.json()["status"]
            print(f"  Status: {status}")

            if status in ("Confirmed", "Completed", "Swept"):
                break
            time.sleep(15)


if __name__ == "__main__":
    create_escrow()
