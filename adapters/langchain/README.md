# kagikai-langchain

LangChain tools for [Kaginet](https://github.com/kaginet/kaginet) Bitcoin escrow.

Exposes 29 tools that let any LangChain agent create, fund, and manage
trustless Bitcoin escrow instruments via the Kaginet Instrument Creation
Service (ICS).

## Install

```bash
pip install kagikai-langchain
```

## Quick start

```python
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_tools_agent
from kagikai_langchain import KagikaiToolkit

toolkit = KagikaiToolkit(
    base_url="https://mcp.kaginet.com",
    api_key="kagi_YOUR_API_KEY",
)
tools = toolkit.get_tools()

llm = ChatOpenAI(model="gpt-4o")
agent = create_openai_tools_agent(llm, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools)
executor.invoke({"input": "Create a 50000 sat escrow to bc1q...recipient"})
```

Get an API key at [cloud.kaginet.com](https://cloud.kaginet.com).

Environment variables `KAGIKAI_BASE_URL` and `KAGIKAI_API_KEY` are used
as fallbacks when constructor args are empty.

## Tools (29)

### Escrow (recommended)

| Tool | Description | Auth |
|------|-------------|------|
| `kagikai_escrow_create` | Create escrow with bc1q funding address | Yes |
| `kagikai_escrow_status` | Check escrow status and txids | Yes |
| `kagikai_escrow_release` | Release: evidence triggers auto-sweep | Yes |
| `kagikai_escrow_cancel` | Cancel/reject an escrow | Yes |
| `kagikai_set_destination` | Set/change sweep destination address | Yes |
| `kagikai_fee_estimate` | Estimate fees for an escrow amount | Yes |

### Vault and recovery

| Tool | Description | Auth |
|------|-------------|------|
| `kagikai_list_available` | List reclaimable instruments | Yes |
| `kagikai_recycle_instrument` | Reuse an expired instrument | Yes |
| `kagikai_refund_instrument` | Refund to source address | Yes |

### Dispute (optimistic settlement)

| Tool | Description | Auth |
|------|-------------|------|
| `kagikai_dispute_instrument` | Dispute with bond deposit | Yes |
| `kagikai_resolve_dispute` | Resolve: uphold/reject/refund | Yes |

### Instruments (advanced)

| Tool | Description | Auth |
|------|-------------|------|
| `kagikai_create_instrument` | Create raw P2TR instrument | Yes |
| `kagikai_confirm_instrument` | Confirm funded instrument | Yes |
| `kagikai_get_status` | Get instrument status | Yes |
| `kagikai_submit_instrument` | Submit deliverable evidence | Yes |
| `kagikai_complete_instrument` | Mark instrument completed | Yes |
| `kagikai_reject_instrument` | Reject instrument | Yes |
| `kagikai_batch_create` | Batch create instruments | Yes |
| `kagikai_batch_status` | Batch status query | Yes |

### Verification and identity

| Tool | Description | Auth |
|------|-------------|------|
| `kagikai_health` | Server health status | No |
| `kagikai_verify_address` | Dual-node address verification | Yes |
| `kagikai_get_attestation` | Get attestation document | No |
| `kagikai_verify_tdx_quote` | Verify TDX attestation | No |
| `kagikai_get_agent` | Get agent identity | No |
| `kagikai_update_agent` | Update agent profile | Yes |
| `kagikai_get_agent_card` | Get A2A Agent Card | No |
| `kagikai_get_reputation` | Get reputation stats | No |
| `kagikai_watch_receipt` | Watch Nostr for transfer receipt | Yes |
| `kagikai_delete_watch` | Cancel receipt watch | Yes |

## TDX verification

The `kagikai_verify_tdx_quote` tool fetches the attestation via REST, then
verifies the TDX quote locally using the `kagikai` SDK. Install it with:

```bash
pip install kagikai-langchain[tdx]
```

If the SDK is not installed, the tool returns the raw attestation with
a clear error message.

## License

See [LICENSE](../../LICENSE). License terms are currently under evaluation.
