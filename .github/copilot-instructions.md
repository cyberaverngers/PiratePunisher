# Copilot / AI agent instructions for PiratePunisher

Short: This repository currently contains only a `README.md` with the short description "email punisher" and has no source code, tests, or CI. Before making architecture choices, always ask the repo owner clarifying questions (language, deployment, intended behaviour).

Key facts discovered (explicit and actionable):
- Only file found: `README.md` (contents: "email punisher"). No `src/`, no `tests/`, no workflows, no package manifests.
- There is no explicit owner/maintainer contact or contribution guidelines in the repo.

Agent rules (what to do first)
1. Ask two clarifying questions before implementing core functionality:
   - What is the desired runtime/language (Node/TypeScript, Python, Go, etc.)?
   - What does "email punisher" mean in concrete terms (e.g., block sender, flag messages, send bounce, automated responses, integrate with provider like SendGrid/SES)?
2. If asked to bootstrap the project and no preference is given, propose an implementation plan and wait for approval. Include a 1-2 paragraph rationale for the chosen stack.

Bootstrapping checklist (if authorized to initialize project)
- Create a minimal README section: Usage, Build, Test, Development, License, Contact.
- Pick a small, testable prototype (one CLI or HTTP endpoint) that demonstrates the core behaviour.
- Add skeleton: `src/`, `tests/`, `README.md` updates, and a simple local run command.
- Add a CI workflow under `.github/workflows/ci.yml` that installs deps and runs tests.
- Use semantic commit messages and create a single focused PR for each atomic change.

Testing & build conventions (project-agnostic guidance to follow if you add a language)
- Node/TypeScript: include `package.json`, `npm test` (or `pnpm`), `tsconfig.json`, linting (ESLint) and `jest` or `vitest` for tests.
- Python: use `pyproject.toml` (poetry or pip-tools), `pytest` and `black`/`ruff` for formatting/linting.
- Ensure CI runs the same commands (e.g., `npm ci && npm test` or `python -m pytest`).

Security & secrets
- Never commit credentials or API keys. Use `GITHUB_SECRET` and instruct owners to add provider keys to repository secrets.
- If asked to integrate with email providers (SMTP, SES, SendGrid), add integration adapters behind a clear interface and document environment variables in `README.md`.

PR quality checklist (must be satisfied before opening PR)
- The PR contains a short description of change and motivation.
- Tests that validate behaviour are added and passing.
- README updated with run/build instructions for the feature.
- Linting/formatting applied and CI passes (or CI workflow added if bootstrapping).

When you can't make a safe assumption
- Ask instead of guessing. Example questions to ask the maintainer: "Should this run as a scheduled job or an HTTP service?" or "Which providers should we support initially (SMTP only, or API providers like SendGrid)?"

Merging & future updates to this document
- If this file exists in the future, merge changes to preserve any human-written policy text—do not replace blindly. Reference this file in PR descriptions when the agent modifies repository layout or CI.

Contact & follow-up
- Ask the repository owner/submitter for acceptance criteria for the MVP.

If anything in this guidance is unclear or you want a different default stack, ask the owner before proceeding. After I make any structural change, I will open a short PR and request explicit approval.
