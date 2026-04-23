---
name: coolify-n8n-deploy
description: Configure and operate Coolify and n8n deployment workflows for this repository. Use when Codex needs to prepare repo-local MCP templates, organize deployment credentials safely, apply the existing Coolify deployment conventions, or guide rollout and validation for services that will run behind Coolify and integrate with n8n.
---

# Coolify N8n Deploy

Use this skill to keep deployment instructions, MCP templates, and access handling in a stable project location instead of transient folders such as `__pycache__/`.

## Workflow

1. Read `references/mcp-setup.md` before touching MCP files.
2. Read `references/coolify-api-notes.md` before planning deployment or API-driven updates.
3. Keep committed files limited to templates and guidance.
4. Put real credentials only in ignored local files or environment variables.
5. Treat MCP as optional operator access. Prefer deterministic scripts and REST API flows for deployment.

## Repository Conventions

- Store reusable MCP templates in `mcp/`.
- Keep the committed file as `mcp/opencode.template.json`.
- Store live local credentials in `mcp/opencode.local.json` or another ignored file.
- Never store tokens in `SKILL.md`, references, or tracked JSON.

## Execution Rules

- If the user has not created a Coolify or n8n token yet, stop at template preparation and list the missing credentials.
- If the user provides real credentials later, wire them into a local ignored config instead of a committed file.
- If deployment work is requested, prefer the existing scripts under `execution/` before creating new ones.

## Outputs

- Updated MCP template files under `mcp/`
- Skill guidance under `skills/coolify-n8n-deploy/`
- Deployment or rollout notes derived from the existing project conventions
