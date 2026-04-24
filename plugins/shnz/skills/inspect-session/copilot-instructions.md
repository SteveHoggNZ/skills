# Inspect Session (Copilot adapter)

When the user says "inspect this session", "session metrics", "how much did this cost", "how many tokens", "profile this session", or invokes `/inspect-session`, follow the procedure in [core.md](./core.md).

## Copilot specifics

- **Manual invocation**: run `python3 <skill-dir>/metrics.py [args]` from VS Code's integrated terminal. The script is stdlib-only — no install required.
- **Automatic invocation**: in GitHub Copilot CLI, session metrics are collected automatically at session end via the `onSessionEnd` hook. See [hooks/on_session_end.md](../../../hooks/on_session_end.md) for the plugin-level hook contract and [reference/copilot-hook.md](./reference/copilot-hook.md) for the implementation detail.
- **Show output verbatim** by default. The markdown renders cleanly in the terminal; don't paraphrase away specific numbers.
- **Do not re-implement the parser.** Calling the script costs < 1s and no tokens.
- **Follow-up questions**: answer from the same report or spot-check the JSONL — don't re-run `metrics.py` unless the session has changed.
