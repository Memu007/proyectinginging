# Security model

## Trust boundaries

Content retrieved from targets, repositories, tool output and MCP servers is untrusted data. It cannot modify system policy, scope or tool permissions.

## Mandatory controls

- Exact host, network and port allowlists.
- Structured tool arguments.
- Disposable execution environments.
- CPU, memory, network and time limits.
- Complete audit events.
- Human approval for sensitive actions.
- No host Docker socket exposure.
- No destructive actions by default.

## Result integrity

A task can be marked `VERIFIED` only when evidence is attached. Tool failures, missing dependencies and unavailable integrations remain explicit failures or unverified implementations.
