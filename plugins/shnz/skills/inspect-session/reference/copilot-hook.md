# Copilot Hook: inspect-session Implementation

The plugin-level hook contract for `onSessionEnd` lives at [../../../hooks/on_session_end.md](../../../hooks/on_session_end.md).

This file contains the **inspect-session-specific implementation detail**: TypeScript and Python examples, output format (`.metrics.json`), aggregation patterns, and deployment notes.

## Architecture

```
plugins/shnz/hooks/on_session_end.md   ← hook contract (event, input/output, registered skills)
plugins/shnz/skills/inspect-session/
└── reference/copilot-hook.md          ← this file (implementation detail for inspect-session)
```

---

## Hook registration (TypeScript)

```typescript
import { CopilotClient } from "@github/copilot-sdk";
import { spawn } from "child_process";
import * as fs from "fs";
import * as path from "path";

const client = new CopilotClient();

const session = await client.createSession({
  hooks: {
    onSessionEnd: async (input, invocation) => {
      const sessionId = input.sessionId;
      const sessionJsonlPath = resolveSessionPath(sessionId);

      if (!fs.existsSync(sessionJsonlPath)) {
        console.error(`Session JSONL not found: ${sessionJsonlPath}`);
        return;
      }

      const metricsPath = path.join(__dirname, "metrics.py");
      const proc = spawn("python3", [metricsPath, sessionJsonlPath, "--json"]);

      let metricsJson = "";
      proc.stdout.on("data", (data) => {
        metricsJson += data.toString();
      });

      proc.on("close", (code) => {
        if (code === 0) {
          const outPath = sessionJsonlPath.replace(/\.jsonl$/, ".metrics.json");
          fs.writeFileSync(outPath, metricsJson);
          console.log(`Metrics written to ${outPath}`);
        } else {
          console.error(`metrics.py exited with code ${code}`);
        }
      });
    },
  },
});

function resolveSessionPath(sessionId: string): string {
  const home = process.env.HOME || process.env.USERPROFILE;
  const projectSlug = process.cwd().replace(/\//g, "-").replace(/^-/, "");
  return path.join(home, ".copilot", "projects", projectSlug, `${sessionId}.jsonl`);
}
```

## Hook registration (Python)

```python
from github_copilot_sdk import CopilotClient
import subprocess
import os
from pathlib import Path

client = CopilotClient()

def on_session_end(input_data, invocation):
    session_id = input_data.get("sessionId")
    session_jsonl_path = resolve_session_path(session_id)

    if not Path(session_jsonl_path).exists():
        print(f"Session JSONL not found: {session_jsonl_path}")
        return

    metrics_py = Path(__file__).parent.parent / "metrics.py"
    result = subprocess.run(
        ["python3", str(metrics_py), session_jsonl_path, "--json"],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        metrics_path = session_jsonl_path.replace(".jsonl", ".metrics.json")
        with open(metrics_path, "w") as f:
            f.write(result.stdout)
        print(f"Metrics written to {metrics_path}")
    else:
        print(f"metrics.py failed: {result.stderr}")

def resolve_session_path(session_id: str) -> str:
    home = Path.home()
    project_slug = os.getcwd().replace("/", "-").lstrip("-")
    return str(home / ".copilot" / "projects" / project_slug / f"{session_id}.jsonl")

session = client.create_session(hooks={"onSessionEnd": on_session_end})
```

## Output: `.metrics.json`

After the hook runs, alongside each session JSONL you get:

```json
{
  "session_id": "15f5fb6d-8170-4a51-90e6-0e4bfd82d7dc",
  "project": "/Users/one/Projects/SteveHoggNZ/skills",
  "model": "claude-opus-4-7",
  "started_at": "2026-04-18T14:03:22Z",
  "ended_at": "2026-04-18T18:57:11Z",
  "duration_seconds": 17629,
  "user_turns": 42,
  "assistant_turns": 89,
  "tool_calls": 231,
  "tokens": {
    "input_non_cached": 12406,
    "output": 187421,
    "cache_read": 4218902,
    "cache_creation_5m": 98344,
    "cache_creation_1h": 12015,
    "cache_hit_rate": 0.973
  },
  "cost": {
    "input_usd": 0.19,
    "output_usd": 14.06,
    "cache_read_usd": 6.33,
    "cache_creation_usd": 2.21,
    "total_usd": 22.79,
    "cost_per_user_turn": 0.54
  },
  "tool_breakdown": { "bash": 72, "edit": 54, "read": 41, "grep": 22 },
  "latency": { "min_seconds": 0.4, "median_seconds": 2.1, "p90_seconds": 11.7, "max_seconds": 47.2 }
}
```

## Optional: aggregation

```python
def aggregate_metrics(metrics_dir: str, output_file: str):
    metrics_path = Path(metrics_dir)
    all_metrics = [json.load(open(f)) for f in metrics_path.glob("*.metrics.json")]
    summary = {
        "total_sessions": len(all_metrics),
        "total_cost_usd": sum(m["cost"]["total_usd"] for m in all_metrics),
        "sessions": all_metrics,
    }
    with open(output_file, "w") as f:
        json.dump(summary, f, indent=2)
```

## Deployment notes

- Hook exceptions must not propagate — log and swallow.
- Adjust `resolve_session_path()` to match your Copilot version's session storage layout.
- Manual `/inspect-session` still works; it shows markdown in real-time. The hook writes JSON for offline querying. Both call the same `metrics.py`.

