# Kaginet Fee Model Reference

## Fee Structure

| Component | Value | Notes |
|-----------|-------|-------|
| Platform fee | 0.5% (50 bps) | Applied to escrow amount |
| Mining fee | Dynamic | Based on mempool congestion |
| Minimum escrow | 2,000 sats | Bitcoin dust limit |
| Maximum escrow | No hard cap | Circuit breaker: 50M sats/day global |

## Fee Calculation

```
total_cost = escrow_amount + platform_fee + mining_fee
platform_fee = escrow_amount * 50 / 10000
mining_fee = estimated_vbytes * sat_per_vbyte
```

## Example

For a 100,000 sat escrow at 10 sat/vbyte:

```
Platform fee:  500 sats (0.5%)
Mining fee:    ~2,500 sats (250 vbytes * 10 sat/vbyte)
Total cost:    103,000 sats
Payee receives: 100,000 sats
```

## Refund Policy

- Expired escrow: refund minus mining fee only (no platform fee)
- Failed evaluation: refund minus mining fee only
- Dispute upheld: full refund to buyer, bond returned

## Dynamic Fee Estimation

Call `kaginet_fee_estimate` with the escrow amount to get real-time fee breakdown including current mempool-based mining fee estimates at three priority levels:

| Priority | Target | Typical |
|----------|--------|---------|
| Economy | ~6 blocks (1 hr) | 5-15 sat/vB |
| Normal | ~3 blocks (30 min) | 10-30 sat/vB |
| Priority | ~1 block (10 min) | 20-100 sat/vB |
