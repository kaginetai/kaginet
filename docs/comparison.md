# Comparison: Kaginet vs Alternatives

## The Landscape

AI agent payment infrastructure falls into two categories:

**Fiat-first**: Stripe, Natural, Coinbase x402, Crossmint. These extend traditional payment rails (cards, bank accounts, stablecoins) for agent use. Mature ecosystems, familiar developer experience, broad wallet/exchange support.

**Crypto-native escrow**: ERC-8183, AURA, Nevermined, Kaginet. These use blockchain-native escrow with programmable conditions. Different tradeoffs around finality, gas costs, and integration complexity.

## Feature Matrix

| Feature | Stripe | ERC-8183 | AURA | Kaginet |
|---|---|---|---|---|
| **Settlement** | Card / fiat | Any ERC-20 | USDC on Base | Bitcoin |
| **Escrow type** | SPT scoped tokens | Smart contract | Smart contract | Taproot P2TR |
| **Settlement finality** | Chargeback window (60+ days) | Block confirmation (seconds on L2) | Block confirmation | Bitcoin confirmation (approximately 10 min) |
| **On-chain cost per escrow** | None (off-chain) | 4+ txs, gas fees | Gas fees | 2 txs, mining fees |
| **Hardware attestation** | No | Via Automata hook | No | Intel TDX (built-in) |
| **MCP server** | Yes (mcp.stripe.com) | No | No | Yes (mcp.kaginet.com) |
| **Framework adapters** | LangChain, CrewAI, OpenAI, Vercel | LangChain, CrewAI | CrewAI | LangChain, CrewAI |
| **Dispute mechanism** | Card chargeback | Via hooks | None | Optimistic + bond |
| **Batch creation** | N/A | N/A | N/A | Up to 20 per batch |
| **Agent reputation** | None | ERC-8004 multi-dim | 8-dimension on-chain | Instrument history |
| **Smart contract risk** | No | Yes | Yes | No |
| **Zero-install integration** | Existing Stripe account | Wallet required | 30-second ghost registration | One MCP URL |

## Practical Tradeoffs

### Kaginet strengths

- **Settlement is final.** Once a Bitcoin transaction confirms, it cannot be reversed. No chargeback window. For agent-to-agent transactions where both parties are software, finality matters more than buyer protection.
- **Hardware-attested escrow.** Intel TDX proves the escrow operator cannot access the keys. This is built-in, not an optional hook. Agents can verify the attestation independently.
- **No smart contract risk.** The escrow is a standard Bitcoin UTXO, not a smart contract. No reentrancy bugs, no governance key exploits, no EVM-specific attack surface.
- **Two on-chain transactions.** Forward (bc1q→bc1p) and sweep (bc1p→payee). Minimal chain footprint. No gas estimation, no approval transactions.
- **MCP-native.** One URL in the agent config. 29 tools available immediately. No SDK installation required for basic use.

### Kaginet limitations

- **Bitcoin-only settlement.** No fiat, no stablecoins. The payer needs bitcoin. This limits use cases where the payer expects card payment.
- **Confirmation time.** Bitcoin blocks average 10 minutes. L2 chains confirm in seconds. For time-sensitive micro-transactions, this latency matters.
- **No streaming/metered billing.** Kaginet handles discrete escrow payments. Stripe's token streaming and Nevermined's metering serve per-API-call billing use cases that Kaginet does not address.
- **Smaller ecosystem.** Stripe has 250M+ Link users and 288 product integrations. ERC-8183 has 30+ chain deployments. Kaginet is a focused tool for a specific use case.

## When to Use Kaginet

- Agent-to-agent payments where settlement finality matters
- Escrows where hardware proof that the operator cannot interfere is valuable
- Bitcoin-denominated agent economies
- Use cases where two on-chain transactions is an acceptable cost for trustless escrow
- Integration via MCP where zero SDK installation is preferred

## When to Use Alternatives

- **Stripe**: consumer-facing agents, card payments, existing Stripe infrastructure
- **ERC-8183**: EVM ecosystem agents, stablecoin settlement, on-chain reputation portability
- **AURA**: fast onboarding (30-second registration), USDC on Base, multi-dimensional reputation
- **Natural**: fiat banking infrastructure for agents, compliance-first use cases
