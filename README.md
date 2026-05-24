# Kaginet — Trustless Bitcoin Escrow for AI Agents

[![CI](https://github.com/kaginet/kaginet/actions/workflows/test-adapters.yml/badge.svg)](https://github.com/kaginet/kaginet/actions)
[![PyPI - kagikai-langchain](https://img.shields.io/pypi/v/kagikai-langchain)](https://pypi.org/project/kagikai-langchain/)
[![PyPI - kagikai-crewai](https://img.shields.io/pypi/v/kagikai-crewai)](https://pypi.org/project/kagikai-crewai/)
[![License](https://img.shields.io/badge/License-See_LICENSE-lightgrey.svg)](LICENSE)

Hardware-attested Bitcoin escrow that AI agents can use via MCP, LangChain, or CrewAI. No custody, no trust assumptions, no counterparty risk.

**Live on Bitcoin mainnet.** Running inside an Intel TDX confidential VM.

---

## Why Kaginet

| Property | How |
|---|---|
| **No custody** | Mathematical lockout: the issuer key is destroyed before funding. Bitcoin consensus enforces this, not policy. |
| **Private** | Off-chain bearer transfers are invisible. No public ledger for intermediate transfers. |
| **Hardware-attested** | Intel TDX proves the code that deleted the key is the audited code. Verifiable against Intel's root CA. |
| **29 MCP tools** | Any MCP-compatible agent (Claude, GPT-4, Cursor, Windsurf) gets payment capability with one URL. |
| **Bitcoin mainnet** | Real money. Live now. Not a testnet demo. |

---

## Quick Start

### Option A: MCP (recommended, zero install)

Add to your Claude Desktop, Cursor, or Windsurf MCP config:

```json
{
  "mcpServers": {
    "kagikai": {
      "url": "https://mcp.kaginet.com/sse",
      "headers": {
        "Authorization": "Bearer kagi_YOUR_API_KEY"
      }
    }
  }
}
```

Get an API key at [cloud.kaginet.com](https://cloud.kaginet.com).

Your agent now has 29 payment tools. Try:

```
Create a 50,000 sat escrow to bc1q...recipient for "Logo design work"
```

### Option B: LangChain

```bash
pip install kagikai-langchain
```

```python
from kagikai_langchain import KagikaiToolkit

toolkit = KagikaiToolkit(
    base_url="https://mcp.kaginet.com",
    api_key="kagi_YOUR_API_KEY",
)
tools = toolkit.get_tools()  # 29 tools ready for your agent
```

### Option C: CrewAI

```bash
pip install kagikai-crewai
```

```python
from kagikai_crewai import (
    KagikaiEscrowCreateTool,
    KagikaiEscrowStatusTool,
    KagikaiEscrowReleaseTool,
)

# Add to your crew's agent
tools = [
    KagikaiEscrowCreateTool(),
    KagikaiEscrowStatusTool(),
    KagikaiEscrowReleaseTool(),
]
```

---

## How It Works

```
Agent Runtime                MCP Server              ICS (TEE Enclave)           Bitcoin
─────────────                ──────────              ─────────────────           ───────
                                                                                    
  kagikai_escrow_create ──▶  Authenticate ──▶  Generate keys inside TDX            
                                               Destroy issuer key (kA)             
                                               Create P2TR escrow address          
                                               Generate bc1q funding addr          
                             ◀── instrument_id + funding_address ◀──               
                                                                                    
  "Fund this address" ────────────────────────────────────────────────▶ bc1q funded
                                                                                    
                                               Watcher detects funding             
                                               Auto-forward bc1q → bc1p    ──────▶ P2TR escrow
                                               Status: Confirmed                   
                                                                                    
  kagikai_escrow_release ─▶  Sign JWT ──────▶  Evaluate evidence                   
                                               Status: Completed                   
                                               Auto-sweep to payee         ──────▶ Payee receives
                                               Zero all keys                       
```

1. **Create**: Agent calls `kagikai_escrow_create` with amount and payee address. ICS generates keys inside the TEE, destroys the issuer key, returns a bc1q funding address.
2. **Fund**: Payer sends bitcoin to the bc1q address from any wallet. ICS auto-forwards to the internal P2TR escrow.
3. **Release**: Agent submits evidence. Evaluator validates (auto or manual). ICS auto-sweeps funds to the payee.
4. **Attest**: At any point, anyone can verify the TDX attestation proving the issuer key was deleted by the audited code.

---

## Instrument Lifecycle

```
Created ──▶ WatchingForFunding ──▶ Forwarding ──▶ Confirmed
                                                      │
                                    ┌─────────────────┤
                                    ▼                  ▼
                                Submitted          Expired
                                    │                  │
                       ┌────────────┼────────────┐     ▼
                       ▼            ▼            ▼  Available
                  Completed    Rejected    DisputeWindow  │
                       │            │            │        ├──▶ Recycled ──▶ Confirmed
                       ▼            ▼            │        └──▶ Refunded (terminal)
                    Swept       Available    ┌───┴───┐
                  (terminal)        │        ▼       ▼
                                    │   Completed  Disputed
                                    │  (auto-win)     │
                                    │            ┌────┴────┐
                                    │            ▼         ▼
                                    │       Completed  Rejected
                                    │      (seller     (buyer
                                    │       wins)       wins)
                                    ▼
                              Recycled / Refunded
```

Full state machine documentation: [docs/instrument-lifecycle.md](docs/instrument-lifecycle.md)

---

## Documentation

| Document | Description |
|---|---|
| [Architecture](docs/architecture.md) | System components, trust boundaries, data flow |
| [Instrument Lifecycle](docs/instrument-lifecycle.md) | State machine with all transitions |
| [API Reference](docs/api-reference.md) | Every REST endpoint with schemas |
| [MCP Tools](docs/mcp-tools.md) | All 29 tool definitions |
| [Attestation](docs/attestation.md) | TDX attestation chain and verification |
| [Dispute Mechanism](docs/dispute-mechanism.md) | Optimistic settlement with bonds |
| [Fee Model](docs/fee-model.md) | Fee structure and estimation |
| [Security Model](docs/security-model.md) | Threat model and trust boundaries |
| [Comparison](docs/comparison.md) | Kaginet vs ERC-8183 vs Stripe vs AURA |
| [Protocol Specification](docs/protocol-spec.md) | Full escrow protocol: state machine, evaluator schemas, Nostr events, MCP tools |

---

## Live Endpoints

| Endpoint | URL |
|---|---|
| MCP (SSE) | `https://mcp.kaginet.com/sse` |
| Developer Dashboard | [cloud.kaginet.com](https://cloud.kaginet.com) |
| Product Website | [kaginet.com](https://kaginet.com) |

---

## Examples

- [quickstart.py](examples/quickstart.py) — Create your first escrow
- [agent-escrow-flow.py](examples/agent-escrow-flow.py) — Full agent-to-agent payment
- [mcp-config.json](examples/mcp-config.json) — MCP client configuration
- [langchain-agent.py](examples/langchain-agent.py) — LangChain agent with payment tools
- [crewai-crew.py](examples/crewai-crew.py) — CrewAI crew with escrow capability
- [verify-attestation.py](examples/verify-attestation.py) — Verify a TDX attestation
- [fee-estimate.py](examples/fee-estimate.py) — Check fees before creating an escrow

---

## Project Structure

```
kaginet/
  adapters/
    langchain/          # pip install kagikai-langchain (29 tools)
    crewai/             # pip install kagikai-crewai (29 tools)
    tests/              # 90 adapter tests
  docs/                 # Architecture, API reference, protocol docs
  examples/             # Integration examples
  verify/               # TDX attestation verification tool
```

The ICS server (Rust, runs inside Intel TDX) is not included in this repository. This repo contains the integration layer: framework adapters, documentation, and examples.

---

## Security

See [SECURITY.md](SECURITY.md) for our responsible disclosure policy.

The security model is documented at [docs/security-model.md](docs/security-model.md).

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). We welcome adapter contributions for new frameworks, documentation improvements, and example code.

---

## License

See [LICENSE](LICENSE). License terms are currently under evaluation.
