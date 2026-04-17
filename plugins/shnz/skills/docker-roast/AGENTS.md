# Docker Roast (Codex adapter)

When the user asks to lint, roast, review, or check a Dockerfile, follow the procedure in [core.md](./core.md).

## Codex specifics

- **Parse `ARGUMENTS` for subcommands** (see core.md §"Subcommand dispatch"): empty → default run, or `examples` / `install` / `help`, else treat as target path.
- **Detect the runner once** via shell (`command -v droast`, then `command -v docker`). Reuse for the rest of the session.
- Use your shell + file-editing tools as usual. Prefer surgical edits when applying approved fixes; don't rewrite whole Dockerfiles.
- Bundled examples live at `<skill-dir>/examples/*.Dockerfile`.
- **Never install or apply fixes without explicit user approval.**
- Keep the roast commentary by default — it's the tool's signature. Strip only when the user asks for `--no-roast`.