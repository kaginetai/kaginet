# Fee Model

Kaginet charges a platform fee on every funded instrument, plus Bitcoin mining fees for on-chain transactions.

## Platform Fee

The platform fee is calculated as basis points of the instrument amount, with minimum and maximum clamps:

```
raw_fee = (amount_sats * fee_basis_points) / 10000
platform_fee = clamp(raw_fee, fee_min_sats, fee_max_sats)
```

| Parameter | Default | Description |
|-----------|---------|-------------|
| `fee_basis_points` | 50 (0.5%) | Fee rate in basis points |
| `fee_min_sats` | 10 sats | Minimum fee (small escrows) |
| `fee_max_sats` | 100,000 sats | Maximum fee cap |

The platform fee is collected as a separate output in the funding transaction. It goes to a dedicated fee collection address.

## Mining Fees

Two on-chain transactions occur per escrow lifecycle:

### Forward transaction (bc1q → bc1p)

- Transaction size: approximately 110 virtual bytes (vB)
- Fee rate: dynamic, from mempool.space `economyFee` tier
- Typical fee: 110-550 sats (at 1-5 sat/vB)

### Sweep transaction (bc1p → payee)

- Transaction size: approximately 111 virtual bytes (vB)
- Fee rate: same as forward
- Typical fee: 111-555 sats (at 1-5 sat/vB)

Total mining fees per escrow: approximately 221-1,110 sats depending on mempool conditions.

## Fee Priority

The mining fee rate is fetched from mempool.space and defaults to the `economy` tier (targeting next-block-ish but not urgent). Configurable tiers:

| Priority | Description |
|----------|-------------|
| `fastest` | Next block target |
| `half_hour` | 30-minute target |
| `hour` | 1-hour target |
| `economy` | Economy tier (default) |
| `minimum` | Minimum relay fee |

For non-urgent escrow operations, the economy tier avoids overpayment during fee spikes.

## Viability Check

At instrument creation, ICS checks that mining fees do not exceed 25% of the instrument amount. If fees would consume more than 25%, the creation is rejected with an error. This prevents uneconomic micro-escrows during fee spikes.

## Fee Estimation

Use the `kagikai_fee_estimate` MCP tool or `GET /admin/fee-config` endpoint to check fees before creating an escrow:

```json
{
  "amount_sats": 50000,
  "platform_fee_sats": 250,
  "platform_fee_bps": 50,
  "effective_rate_pct": 0.5,
  "mining_fee_forward_sats": 220,
  "mining_fee_sweep_sats": 222,
  "mining_fee_total_sats": 442,
  "total_cost_sats": 692,
  "net_to_recipient_sats": 49308,
  "viable": true
}
```

## Examples

| Escrow Amount | Platform Fee | Mining Fees (est.) | Total Cost | Net to Recipient |
|---------------|-------------|-------------------|------------|-----------------|
| 2,000 sats | 10 sats (min) | 442 sats | 452 sats | 1,548 sats |
| 10,000 sats | 50 sats | 442 sats | 492 sats | 9,508 sats |
| 50,000 sats | 250 sats | 442 sats | 692 sats | 49,308 sats |
| 100,000 sats | 500 sats | 442 sats | 942 sats | 99,058 sats |
| 1,000,000 sats | 5,000 sats | 442 sats | 5,442 sats | 994,558 sats |
| 10,000,000 sats | 50,000 sats | 442 sats | 50,442 sats | 9,949,558 sats |
| 100,000,000 sats | 100,000 sats (max) | 442 sats | 100,442 sats | 99,899,558 sats |

Mining fee estimates assume 2 sat/vB economy rate. Actual fees vary with mempool conditions.
