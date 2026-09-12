# Security policy

This public repository is an engineering lab and contains no production credentials or customer data.

Please report a suspected vulnerability privately through GitHub Security Advisories rather than opening a public issue with exploit details or secrets.

## Security principles

- Never commit `.env`, API keys, tokens, credentials or production payloads.
- Treat model/tool output as untrusted input.
- Keep side-effect authority outside model prompts.
- Prefer least-privilege adapters and explicit allowlists when connecting tools.
- Redact operational/customer content from logs and examples.
