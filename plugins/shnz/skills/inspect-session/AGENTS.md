# Inspect Session (Codex adapter)

When the user says "inspect this session", "session metrics", "how much did this cost", "how many tokens", "profile this session", or invokes `/inspect-session`, follow the procedure in [core.md](./core.md).

## Codex specifics

- **Run the bundled script**: `python3 <skill-dir>/metrics.py [args]`. The script is stdlib-only — no `pip install`, no runtime deps.
- **Parse arguments**: accept an optional session UUID, an absolute path to a `.jsonl`, or nothing (defaults to the most recent session in the current project). A trailing `--json` flag switches output to machine-readable JSON.
- **Show output verbatim** (or near-verbatim). The markdown renders cleanly in the terminal; don't paraphrase away specific numbers.
- **Do not re-implement the parser.** Calling the script costs < 1s and no tokens. Hand-parsing large JSONLs in conversation costs thousands of tokens and invites rounding errors.
- **Follow-up questions**: answer from the same report or spot-check the JSONL with grep — don't re-run `metrics.py` unless the session has changed.
