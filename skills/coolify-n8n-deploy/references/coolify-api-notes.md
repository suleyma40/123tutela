# Coolify API Notes

Use these notes when deploying or updating services through Coolify.

## Deployment policy

- Prefer the Coolify REST API for repeatable deployment flows.
- Treat MCP access as an operator convenience for discovery and diagnostics, not the primary deployment path.
- Keep application repositories private.

## API behaviors already observed

- Create a private GitHub-backed app with `POST /api/v1/applications/private-github-app`.
- Send separate `PATCH` requests for different fields. Combining unrelated updates is unreliable.
- Remove a public URL with `PATCH {"domains": ""}`.
- Set Docker network aliases with `PATCH {"custom_network_aliases": "alias-name"}`.
- When env vars drift, delete the old variable and create a new one instead of relying on patch semantics.
- Trigger deployment with `GET /api/v1/deploy?uuid={uuid}&force=true`.

## Security defaults

- Prefer internal-only services whenever possible.
- Require an API key only when a service is public or there is a concrete cross-network risk.
- If an API key is needed, generate it at runtime and store it outside the repository.

## Operational sequence

1. Create or update the app definition.
2. Apply env vars and network aliases.
3. Deploy.
4. Validate health endpoints.
5. Remove temporary public exposure if the service should stay internal.
