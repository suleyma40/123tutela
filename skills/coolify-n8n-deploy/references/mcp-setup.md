# MCP Setup

Use this reference when the task requires repo-local MCP configuration for Coolify or n8n.

## Required inputs

- Coolify base URL
- Coolify access token
- n8n base URL
- n8n API key or bearer token

Do not commit real values. Store only templates in the repository.

## Repository layout

- Keep reusable MCP templates in `mcp/`.
- Keep skill guidance in `skills/coolify-n8n-deploy/`.
- Keep real secrets in ignored local files such as `mcp/opencode.local.json` or environment variables.

## Template policy

- Commit `*.template.json` files only.
- Ignore `*.local.json` and any file that contains live credentials.
- Keep environment variable names stable so local tooling can inject secrets consistently.

## Recommended local file flow

1. Copy `mcp/opencode.template.json` to `mcp/opencode.local.json`.
2. Replace placeholder values with real local secrets.
3. Point the MCP-capable client to the local file.
4. Verify access against Coolify and n8n before relying on it for operations.

## Coolify environment names

- `COOLIFY_ACCESS_TOKEN`
- `COOLIFY_BASE_URL`

## n8n environment names

- `N8N_BASE_URL`
- `N8N_API_KEY`

## Constraints

- MCP availability depends on the client running the session. A repo file alone does not activate MCP.
- If the client does not load repo-local MCP configs, copy the same values into the client's supported config location.
