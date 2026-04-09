# Reuse Pipeline-Generic as an iOS CI/CD template

This document is the **flat manifest** for humans and agents. The canonical implementation lives in this repository (or your fork): `.github/workflows/ios.yml` plus `ios-job-*.yml`, `ios-release.yml`, Cursor rules under `.cursor/rules/`, `fastlane/`, and Ruby `Gemfile`.

## When you only have a repo URL

| Goal | What to do |
|------|------------|
| **New empty remote** for an app you are about to create or already have locally | Open the **app** folder in Cursor, merge template files (see [SETUP_IOS_DEVOPS_KIT.md](SETUP_IOS_DEVOPS_KIT.md)), then paste **`CURSOR_IOS_DEVOPS_BOOTSTRAP_PROMPT.txt`** and include the **clone URL** in chat so the agent runs `git remote` + `git push`. |
| **Existing app repo** (clone URL) | Clone the app, open repo root in Cursor, paste **`CURSOR_IOS_DEVOPS_APPLY_TEMPLATE_PROMPT.txt`**, fill **TEMPLATE_ROOT** (path to this template clone) and **TARGET_REMOTE_URL** (optional). |
| **Template already copied**; you only need remote + push | Use the **minimal variant** at the bottom of **`CURSOR_IOS_DEVOPS_APPLY_TEMPLATE_PROMPT.txt`**. |

Agents must follow **`ios-devops-remote-agent-must-push.mdc`**: if a URL is pasted, they run `git remote` and `git push` in the terminal; they do not hand off remote setup as “manual only” unless push failed after a real attempt.

## Files to copy into another project

| Path | Role |
|------|------|
| `.cursor/rules/*.mdc` | Cursor agent ordering, CI reference, Git bootstrap, simulator artifact instructions |
| `.github/workflows/ios.yml` | Orchestrator (`workflow_call` to reusable jobs) |
| `.github/workflows/ios-job-*.yml` | Lint, security, simulator `.app`, tests + coverage |
| `.github/workflows/ios-release.yml` | Base64 P12 + profile secrets + `gym`; optional TestFlight |
| `.github/workflows/ios-code-health.yml` | Reports artifact |
| `.github/workflows/codeql-swift.yml` | CodeQL Swift |
| `.github/dependabot.yml` | Weekly Actions bumps |
| `.github/scripts/` | Simulator UDID helper, code-health scripts |
| `.semgrep/` | Semgrep rule packs used by `ios-job-security.yml` (`mobile.yml`, `ci.yml`, `sentinel.yml`) |
| `Gemfile`, `Gemfile.lock`, `fastlane/` | Fastlane + Bundler on CI |
| `.swiftlint.yml`, `.swiftformat` | Lint/format configs (edit paths after copy) |
| `GITIGNORE_APPEND.txt` | Append to app `.gitignore` |
| `CURSOR_IOS_DEVOPS_BOOTSTRAP_PROMPT.txt` | Paste after files are in the app repo |
| `CURSOR_IOS_DEVOPS_APPLY_TEMPLATE_PROMPT.txt` | Paste to copy from template + bootstrap in one go |
| `SETUP_IOS_DEVOPS_KIT.md` | Human setup steps |
| This file | Manifest + quick routing |

**Do not copy** the template sample app tree `PipelineGeneric/` into another product unless you intend to replace that product’s sources.

## Placeholders to replace

Workflows and `Fastfile` in this repo use **`PipelineGeneric`**, **`PipelineGeneric/`**, **`com.codeandtheory.PipelineGeneric`**, and artifact names derived from the scheme. After copying, run discovery on the target `project.pbxproj` and shared schemes, then align every reference (see **`github-actions-ios-ci.mdc`**).

## Copy-paste prompts (short index)

1. **`CURSOR_IOS_DEVOPS_APPLY_TEMPLATE_PROMPT.txt`** — Template not yet in app repo; supply template path + optional remote URL.
2. **`CURSOR_IOS_DEVOPS_BOOTSTRAP_PROMPT.txt`** — Files already merged; rewire names/paths + Git.
3. **Continue** / **minimal** blocks — Inside those `.txt` files for follow-up messages.
