---
name: dump
description: "Generate focused code context bundles using repomix for third-party AI tools. Use when the user says /context-dump, context dump, export context, create context for, need context about, bundle for [AI tool], or wants to share codebase context externally."
argument-hint: "Describe the topic, feature, or area you need context for"
---

# Context Dump Skill

Generate focused repomix context bundles from the current workspace for use in third-party AI tools (ChatGPT, Gemini, Claude, etc.).

## Procedure

### 1. Analyze the Description

Parse the user's description to understand what parts of the codebase they need context for.

### 2. Explore the Workspace

Use search tools to identify the relevant files and directories:
- **Semantic search** for concept-level matches (e.g., "authentication flow")
- **Grep search** for specific symbols, class names, or patterns
- **File search** for known file/path patterns
- **List directory** to understand project structure

**Use LSP when available.** If a Language Server Protocol server is active for the project's language, use it to improve accuracy:
- `goToDefinition` / `findReferences` to trace symbol usage across the codebase
- `documentSymbol` to understand file structure without reading every line
- `incomingCalls` / `outgoingCalls` to map call chains for a given function

LSP results are more precise than grep for type-aware languages (TypeScript, Go, C#, Java, Rust). Use them to avoid missing indirect dependencies or including false positives from string matches.

### 3. Scan for Documentation

Before building the include list, check for documentation and specification directories that provide context beyond the code itself. Scan for:

- **Project docs:** `docs/`, `doc/`, `documentation/`, `wiki/`
- **Specifications:** `spec/`, `specs/`, `spec-kit/`, `specifications/`, `openapi/`, `swagger/`
- **Architecture:** `adr/`, `architecture/`, `design/`, `.arc42/`
- **AWS AI DLC / ML assets:** `ai-dlc/`, `dlc/`, `sagemaker/`, `models/`, `notebooks/`, `pipelines/`
- **Infrastructure:** `infra/`, `terraform/`, `cdk/`, `cloudformation/`, `pulumi/`
- **Root-level docs:** `README.md`, `CLAUDE.md`, `AGENTS.md`, `ARCHITECTURE.md`, `CONTRIBUTING.md`, `CHANGELOG.md`

Include relevant documentation in the bundle — or as a separate docs bundle if it's substantial. Documentation often provides the "why" that code alone cannot convey.

Build a list of include paths (files, directories, or glob patterns) that cover the requested topic. Be focused — include only what's relevant, not the entire codebase.

### 3. Determine Ignore Patterns

Construct ignore patterns to exclude noise. Common defaults:
- Test files: `**/*_test.go`, `**/*.test.ts`, `**/*.test.tsx`, `**/*.spec.ts`, `**/Tests/**`
- Build artifacts: `**/bin/**`, `**/obj/**`, `**/node_modules/**`, `**/dist/**`
- Generated files: `**/*.gen.go`, `**/*.pb.go`, `**/*.designer.cs`

Adjust based on the project's language and framework.

### 4. Generate the Bundle

Run repomix via npx to create the context file:

```bash
npx --yes repomix \
  --include "path/to/dir1,path/to/file.cs,src/feature/**/*.ts" \
  --ignore "**/*.test.ts,**/bin/**,**/obj/**" \
  --output "/tmp/ctx-$(date +%Y%m%d-%H%M%S)-<label>.xml"
```

**Rules:**
- `--include` takes comma-separated paths (no spaces after commas). Supports globs.
- `--ignore` takes comma-separated glob patterns for exclusion.
- `--output` always writes to `/tmp/` with format `ctx-{timestamp}-{label}.xml`.
- Always use `--yes` to skip interactive prompts.
- The `<label>` should be a short kebab-case slug derived from the description (e.g., `auth-flow`, `cart-service`, `api-handlers`).

**For large topics**, split into multiple bundles with a shared timestamp:

```bash
export TS=$(date +%Y%m%d-%H%M%S)

npx --yes repomix \
  --include "docs/**,README.md,CLAUDE.md" \
  --output "/tmp/ctx-${TS}-docs.xml"

npx --yes repomix \
  --include "src/Services/Orders/**,src/Core/Domain/Orders/**" \
  --ignore "**/bin/**,**/obj/**" \
  --output "/tmp/ctx-${TS}-orders-service.xml"
```

### 5. Report Results

After generation, show:
1. Output file path(s) and size(s)
2. What was included (brief summary)
3. Total context size
4. Warning if any bundle exceeds 1MB — suggest splitting

## Size Guidelines

- Target each bundle under 500KB, hard limit 1MB
- If too large, split into sub-bundles (e.g., docs vs code, backend vs frontend)
- Start minimal — the user can request more

## Troubleshooting

### npm/npx Issues
If npx fails with permission or cache errors, try:
```bash
npm cache clean --force
npx --yes repomix --version
```

### Repomix Not Found
Repomix is installed on-demand via npx. The `--yes` flag auto-accepts the install prompt. If it still fails, install globally:
```bash
npm install -g repomix
```
