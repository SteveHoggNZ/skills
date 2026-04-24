# Hook: `onSessionEnd`

Fires when a GitHub Copilot CLI session ends. Use this hook to run cleanup, write metrics, or trigger post-session summaries without requiring user intervention.

## What this hook is for

Skills that produce useful summary data at session close can register here. The primary skill using this hook is **[inspect-session](../skills/inspect-session/)**, which automatically computes token, cost, and latency metrics and writes them to a `.metrics.json` file.

Any future skill that benefits from automatic session-close behaviour (e.g. committing a session log, generating a summary) should also document its integration here.

## Contract

| Field | Description |
|-------|-------------|
| **Event name** | `onSessionEnd` |
| **Fires** | After the Copilot CLI session terminates |
| **Input** | `{ sessionId: string }` |
| **Output** | Void (side-effects only — write files, log, trigger aggregation) |
| **Error handling** | Hook exceptions must not propagate to the caller; log and swallow |

## Registered skills

| Skill | What it does on session end |
|-------|-----------------------------|
| [inspect-session](../skills/inspect-session/) | Runs `metrics.py` against the session JSONL and writes `<session-id>.metrics.json` |

## Registration pattern

```typescript
import { CopilotClient } from "@github/copilot-sdk";

const session = await client.createSession({
  hooks: {
    onSessionEnd: async (input, invocation) => {
      // Each registered skill handler runs here.
      // Keep each handler independent; one failure must not block others.
      await runInspectSessionHook(input.sessionId);
    },
  },
});
```

For the full inspect-session hook implementation (TypeScript + Python examples, output format, aggregation), see [../skills/inspect-session/reference/copilot-hook.md](../skills/inspect-session/reference/copilot-hook.md).

## Adding a new skill to this hook

1. Implement the handler in the skill directory.
2. Document the skill's session-end behaviour in its own `reference/` file.
3. Register the handler in this file's "Registered skills" table above.
