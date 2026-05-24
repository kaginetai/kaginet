"""
Agent-to-agent escrow: full payment lifecycle.

Demonstrates: create escrow, fund, submit evidence, auto-complete, sweep.
Uses hash_match evaluator for fully automated release.

Prerequisites:
    pip install httpx
    export KAGINET_API_KEY=kagi_your_api_key_here
"""

import hashlib
import os
import time

import httpx

BASE = "https://mcp.kaginet.com"
API_KEY = os.environ["KAGINET_API_KEY"]
HEADERS = {"Authorization": f"Bearer {API_KEY}"}


def agent_escrow_flow():
    """Simulate a buyer agent paying a seller agent for work."""

    # The evidence the seller will provide (e.g. a file hash, API response hash)
    evidence = "the-completed-work-output"
    evidence_hash = hashlib.sha256(evidence.encode()).hexdigest()

    with httpx.Client(timeout=30.0) as client:
        # --- Buyer agent: create escrow ---
        print("[Buyer] Creating escrow...")
        resp = client.post(
            f"{BASE}/v1/escrow",
            json={
                "amount_sats": 50_000,
                "payee_address": "bc1qselleraddresshere",
                "description": "Logo design: 3 concepts, 1 final",
                "evaluator_type": "hash_match",
                "evidence_hash": evidence_hash,
            },
            headers=HEADERS,
        )
        resp.raise_for_status()
        escrow = resp.json()
        instrument_id = escrow["instrument_id"]
        print(f"[Buyer] Escrow {instrument_id}")
        print(f"[Buyer] Fund {escrow['amount_sats']} sats to {escrow['funding_address']}")

        # --- Wait for funding (manual step) ---
        print("\n[System] Waiting for on-chain funding...")
        while True:
            s = client.get(f"{BASE}/v1/instruments/{instrument_id}", headers=HEADERS)
            status = s.json()["status"]
            if status == "Confirmed":
                print("[System] Instrument confirmed on-chain")
                break
            if status in ("Completed", "Swept", "Rejected"):
                print(f"[System] Terminal status: {status}")
                return
            time.sleep(15)

        # --- Verify TDX attestation ---
        print("\n[Buyer] Verifying TDX attestation...")
        att = client.get(f"{BASE}/v1/attestation/{instrument_id}")
        att_data = att.json()
        print(f"[Buyer] Attestation mode: {att_data.get('mode')}")
        print(f"[Buyer] Code hash: {att_data.get('code_hash', 'N/A')}")

        # --- Seller agent: submit evidence ---
        print("\n[Seller] Submitting evidence...")
        submit = client.post(
            f"{BASE}/v1/instruments/{instrument_id}/submit",
            json={"evidence": evidence},
            headers=HEADERS,
        )
        submit.raise_for_status()
        result = submit.json()
        print(f"[Seller] Submit result: {result['status']}")

        # hash_match evaluator auto-completes if evidence matches
        if result["status"] == "Completed":
            print("[System] Evidence matched. Auto-sweeping to payee...")

        # --- Poll for sweep ---
        while True:
            s = client.get(f"{BASE}/v1/instruments/{instrument_id}", headers=HEADERS)
            status = s.json()["status"]
            print(f"[System] Status: {status}")
            if status == "Swept":
                print("[System] Funds delivered to seller. Done.")
                break
            time.sleep(15)


if __name__ == "__main__":
    agent_escrow_flow()
