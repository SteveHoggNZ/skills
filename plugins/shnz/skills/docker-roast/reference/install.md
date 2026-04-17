# Install options for `droast`

Pick the lightest path that works in the user's environment. The skill works **without any of these** as long as Docker is available (the default runner falls back to the official image). Only install if the user specifically wants a local binary.

## Option matrix

| Option | When to recommend | Cost | Command |
|---|---|---|---|
| **Docker image** (no install) | Docker is available. Default for this skill. | Zero install; ~20 MB image pulled on first run. | `docker run --rm -v "$(pwd)/Dockerfile":/Dockerfile ghcr.io/immanuwell/droast /Dockerfile` |
| **Homebrew** | macOS or Linuxbrew user. | One-time tap + install; fast. | `brew tap immanuwell/droast git@github.com:immanuwell/homebrew-droast.git` then `brew install immanuwell/droast/droast` |
| **Cargo** | Rust toolchain already installed; no brew. | Compiles from source — 2–5 min first time. | `cargo install dockerfile-roast` |
| **Prebuilt binary** | No package manager, no Docker, no Rust. | Manual download + PATH entry. | Grab from https://github.com/immanuwell/dockerfile-roast/releases and `chmod +x` |

## Recommendation logic (for the skill)

When the user runs `/docker-roast install`, decide the recommendation like this:

```
OS = uname -s  # Darwin / Linux / MINGW*
has_brew   = command -v brew   && echo yes
has_cargo  = command -v cargo  && echo yes
has_docker = command -v docker && echo yes

if has_docker && not has_brew && not has_cargo:
  "You already have a working runner — Docker. No install needed. This skill will use the ghcr image automatically."
elif OS == Darwin && has_brew:
  recommend brew
elif has_cargo:
  recommend cargo + note the compile time
elif has_docker:
  "Docker works as-is; install is optional. If you want a local binary, try cargo or the prebuilt releases."
else:
  recommend prebuilt binary + link to releases
```

The skill should **ask** before running any install command. `cargo install` in particular is slow and consumes a few hundred MB of build artifacts.

## Verifying the install

After install, `droast --version` should print the version string. If it doesn't resolve, the binary isn't on `PATH` — check:

- Homebrew: `brew doctor` often explains missing PATH shims.
- Cargo: `cargo install` places binaries in `$CARGO_HOME/bin` (default `~/.cargo/bin`); this needs to be on PATH.
- Prebuilt: the user likely needs to move the binary somewhere on PATH (`/usr/local/bin` or a directory already on their PATH).

## CI / GitHub Action

The skill doesn't need to cover this — it's separate from the interactive linting use case. But if the user asks, point them at the `immanuwell/dockerfile-roast` GitHub Action:

```yaml
- uses: immanuwell/dockerfile-roast@1.0.0
  with:
    files: '**/Dockerfile'
    min-severity: warning
    no-fail: false   # set true for advisory-only mode
```

The action produces inline PR annotations automatically.

## Uninstall

- Homebrew: `brew uninstall immanuwell/droast/droast` + `brew untap immanuwell/droast`.
- Cargo: `cargo uninstall dockerfile-roast`.
- Prebuilt: `rm $(command -v droast)`.
