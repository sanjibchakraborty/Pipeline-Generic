# Install the Pipeline-Generic iOS pipeline into another Xcode repo

This repository **is** the template (same role as a distributable `ios-devops-cursor-kit` folder). You merge **infrastructure only** into your app’s root so `.github/workflows/` and `.cursor/rules/` sit next to your `.xcodeproj`.

## Step 1 — Copy from Pipeline-Generic

On your machine, have a clone of **Pipeline-Generic** (this repo or your fork) at `TEMPLATE_ROOT`. Open a terminal **in your app’s repository root** (where your `.xcodeproj` lives).

**Recommended — copy only known paths** (avoids copying the sample app `PipelineGeneric/`):

```bash
TEMPLATE_ROOT="/absolute/path/to/Pipeline-Generic"

rsync -a "$TEMPLATE_ROOT/.cursor/" "./.cursor/"
rsync -a "$TEMPLATE_ROOT/.github/" "./.github/"
rsync -a "$TEMPLATE_ROOT/.semgrep/" "./.semgrep/"
rsync -a "$TEMPLATE_ROOT/fastlane/" "./fastlane/"
cp "$TEMPLATE_ROOT/Gemfile" "$TEMPLATE_ROOT/Gemfile.lock" ./
test -f "$TEMPLATE_ROOT/.swiftformat" && cp "$TEMPLATE_ROOT/.swiftformat" ./
cp "$TEMPLATE_ROOT/.swiftlint.yml" ./
cp "$TEMPLATE_ROOT/GITIGNORE_APPEND.txt" \
   "$TEMPLATE_ROOT/CURSOR_IOS_DEVOPS_BOOTSTRAP_PROMPT.txt" \
   "$TEMPLATE_ROOT/CURSOR_IOS_DEVOPS_APPLY_TEMPLATE_PROMPT.txt" \
   "$TEMPLATE_ROOT/CURSOR_IOS_DEVOPS_REUSE.md" \
   "$TEMPLATE_ROOT/SETUP_IOS_DEVOPS_KIT.md" \
   ./
```

**Finder:** open `Pipeline-Generic`, copy the folders and files above into your app root and merge when prompted.

**Then:** append any lines from **`GITIGNORE_APPEND.txt`** that are not already in your app’s **`.gitignore`**.

### Nested kit folder

If you ever have both **`ios-devops-cursor-kit/.github/`** and **root `.github/`**, delete the nested **`ios-devops-cursor-kit/`** after the root copy is complete. GitHub Actions only loads workflows from **`.github/` at the repository root**.

## Step 2 — Cursor Agent (bootstrap)

1. Open your **app** repository root in Cursor.
2. Open **`CURSOR_IOS_DEVOPS_BOOTSTRAP_PROMPT.txt`**.
3. Copy from the line after the first separator through **`END BOOTSTRAP`**.
4. Paste into **Cursor → Agent**. If you already have an **empty** remote, paste its **HTTPS or SSH clone URL** in the same message so the agent can run `git remote` + `git push`.

**One-shot alternative:** if you prefer a single message that includes “copy from template + bootstrap,” use **`CURSOR_IOS_DEVOPS_APPLY_TEMPLATE_PROMPT.txt`** instead (fill in **TEMPLATE_ROOT** and optional **TARGET_REMOTE_URL**).

If the agent stops early, use the **Continue** block in the bootstrap prompt file.

## Remote (minimal steps for you)

1. Create an **empty** repository on GitHub (or your host); copy its **clone URL**.
2. Paste that URL when the agent asks (or include it in the apply-template prompt).
3. The agent should run `git remote add` / `set-url` and `git push -u` for you. If push fails, fix authentication (`gh auth login`, SSH, or HTTPS credentials), then ask the agent to **retry**.

## After bootstrap

- Configure **GitHub Actions secrets** for Match / App Store Connect when you want archive + TestFlight (see **`README.md`**).
- Download Simulator build artifacts using **`ios-ci-artifact-simulator.mdc`**.

## Maintainers

When you change workflows or rules in **Pipeline-Generic**, downstream apps only pick up updates when someone re-copies or merges those paths again—there is no automatic sync. Optionally maintain a small script in this repo to rsync into a separate distributable folder if your team uses zip exports.
