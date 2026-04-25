---
name: dump
kind: procedure
description: "Generate focused code context bundles using repomix for third-party AI tools. Use when the user says /dump, context dump, export context, create context for, need context about, bundle for [AI tool], or wants to share codebase context externally."
argument-hint: "Describe the topic, feature, or area you need context for"
---

<!-- Claude Code adapter — the canonical procedure lives in core.md -->

Follow the full procedure defined in [core.md](./core.md) in this skill's directory.

Use all available Claude Code tools: Glob, Grep, Read, LSP, Bash, and Agent (for deep exploration). Prefer LSP over grep when a language server is active.
