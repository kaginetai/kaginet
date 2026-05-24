# Dispute Mechanism

Kaginet supports optimistic settlement with dispute bonds. This allows fast settlement in the common case (no dispute) while providing a recourse path when the buyer disagrees with the seller's delivery.

## Evaluator Types

The evaluator determines how evidence is judged when an instrument is released.

### hash_match

Automatic evaluation. The evidence SHA-256 hash must match the `expected_hash` in the evaluator config.

- Evidence submitted → hash computed → match/no-match → Completed or Rejected
- No dispute window. Deterministic.

### human_approval

Manual evaluation. A human (or agent) must explicitly call complete or reject.

- Evidence submitted → waits for `POST /v1/instrument/complete` or `/reject`
- 72-hour approval timeout. If no decision within 72 hours, the instrument auto-expires to Available (funds safe, can be refunded).

### optimistic

Automatic approval with a dispute window. The seller is assumed to have delivered correctly unless the buyer disputes.

- Evidence submitted → DisputeWindow opens
- If no dispute within the window: seller auto-wins, funds sweep to payee
- If buyer disputes: bond posted, evaluator resolves

## Optimistic Settlement Flow

```
Confirmed
    │
    ▼ POST /v1/instrument/submit (evidence)
Submitted
    │
    ▼ (optimistic evaluator)
DisputeWindow
    │
    ├──── (window expires, no dispute) ────▶ Completed ──▶ Swept
    │
    └──── POST /v1/instrument/dispute ────▶ Disputed
                                               │
                                 POST /v1/instrument/resolve
                                               │
                              ┌────────────────┼────────────────┐
                              ▼                ▼                ▼
                          "uphold"         "reject"         "refund"
                        Buyer wins       Seller wins      Voluntary
                        Refund +         Sweep +          Refund +
                        bond return      bond to seller   bond return
```

## Configuration

When creating an instrument with the optimistic evaluator:

```json
{
  "amount_sats": 100000,
  "evaluator_type": "optimistic",
  "evaluator_config": {
    "dispute_window_blocks": 432,
    "bond_percent_bps": 1000,
    "resolution_window_blocks": 1008
  }
}
```

| Parameter | Default | Description |
|-----------|---------|-------------|
| `dispute_window_blocks` | 432 (approximately 3 days) | Blocks the buyer has to file a dispute |
| `bond_percent_bps` | 1000 (10%) | Bond amount as basis points of the escrow amount |
| `resolution_window_blocks` | 1008 (approximately 7 days) | Blocks to resolve after dispute filed |

## Dispute Process

### 1. Buyer files dispute

```
POST /v1/instrument/dispute
{
  "instrument_id": "<escrow-uuid>",
  "reason": "Deliverable does not match the agreed specification"
}
```

This creates a **bond instrument**: a separate ICS-native escrow that the buyer must fund. The bond amount is a percentage of the original escrow (default 10%).

The bond prevents frivolous disputes. If the dispute is rejected, the seller receives both the escrow AND the bond.

### 2. Buyer funds the bond

The dispute response includes a `bond_funding_address` (bc1q). The buyer sends the bond amount to this address. The bond instrument goes through the same ICS-native funding pipeline (bc1q → bc1p forward).

### 3. Resolution

An evaluator agent or admin resolves the dispute:

```
POST /v1/instrument/resolve
{
  "instrument_id": "<escrow-uuid>",
  "resolution": "uphold",
  "evidence": "Deliverable does not meet specification per agreed terms"
}
```

| Resolution | Escrow funds | Bond funds |
|------------|-------------|------------|
| `uphold` (buyer wins) | Refunded to buyer | Returned to buyer |
| `reject` (seller wins) | Swept to seller | Swept to seller |
| `refund` (seller voluntary) | Refunded to buyer | Returned to buyer |

### 4. Auto-resolution

If no resolution within the resolution window (default 7 days), the dispute auto-resolves in favor of the seller. This prevents funds from being locked indefinitely.

## Game Theory

The bond mechanism creates a cost to dispute:

- **Honest buyer, bad delivery**: buyer disputes, posts bond, evaluator upholds. Buyer recovers escrow + bond. Net cost: zero.
- **Honest seller, frivolous dispute**: buyer disputes, posts bond, evaluator rejects. Seller keeps escrow + wins bond. Buyer loses bond.
- **Dishonest buyer, good delivery**: buyer must risk 10% of the escrow amount to dispute. If the evaluator rejects the dispute, the buyer loses the bond.

The bond percentage is configurable per instrument. Higher bond = stronger deterrent against frivolous disputes.
