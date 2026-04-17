# Docker Roast (Copilot adapter)

When the user asks to lint, roast, review, or check a Dockerfile, follow the procedure in [core.md](./core.md).

## Copilot specifics

- **Parse `ARGUMENTS` for subcommands** (see core.md §"Subcommand dispatch"): empty → default run, or `examples` / `install` / `help`, else treat as target path.
- **Detect the runner once** from VS Code's integrated terminal (`command -v droast`, then `command -v docker`). Reuse.
- Use VS Code's file tools for reading the target Dockerfile + applying approved fixes. Prefer surgical edits.
- Bundled examples live at `<skill-dir>/examples/*.Dockerfile`.
- **Never install or apply fixes without explicit user approval.**
- Keep the roast commentary by default — it's the tool's signature. Strip only when the user asks for `--no-roast`.