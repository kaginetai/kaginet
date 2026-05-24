# Security Policy

## Reporting a Vulnerability

Kaginet handles real Bitcoin on mainnet. We take security seriously.

If you discover a security vulnerability, please report it responsibly:

**Contact:** [kaginet.com](https://kaginet.com) (use the contact form for security reports)

**What to include:**
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if you have one)

**What we commit to:**
- Acknowledge receipt within 24 hours
- Provide an initial assessment within 72 hours
- Keep you informed of progress
- Credit you in the fix (unless you prefer anonymity)

## Scope

The following are in scope for security reports:

- MCP server endpoint (`mcp.kaginet.com`)
- Dashboard API (`cloud.kaginet.com/api`)
- ICS REST API (any `/v1/*` endpoint)
- Adapter packages (`kagikai-langchain`, `kagikai-crewai`)
- TDX attestation verification logic

## Out of Scope

- The Logto authentication service (report to [Logto](https://logto.io))
- Bitcoin protocol vulnerabilities (report to [Bitcoin Core](https://bitcoincore.org/en/contact/))
- Social engineering attacks
- Denial of service via high-volume requests (rate limited)

## Security Architecture

See [docs/security-model.md](docs/security-model.md) for the full threat model and trust boundaries.

Key properties:
- Private keys exist only inside the Intel TDX enclave
- Issuer key (kA) is destroyed before funding, proven by TDX attestation
- Taproot 2-of-2 escrow with CLTV recovery path
- Per-developer API key authentication with SHA-256 hashing
- Ed25519 JWT signing for ICS API calls
- Circuit breaker on vault withdrawals
- Rate limiting on all endpoints
