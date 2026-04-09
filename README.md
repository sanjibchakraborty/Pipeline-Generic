# Pipeline-Generic

Sample iOS app (**PipelineGeneric**) with GitHub Actions CI/CD: reusable jobs, Fastlane **`gym`** with **distribution certificate + App Store provisioning profile** from GitHub Actions secrets (same pattern as base64 P12 + profile in YAML), optional **TestFlight** upload, **SwiftLint**-based code health, and **CodeQL**.

## Workflows

| Workflow | When | What |
|----------|------|------|
| [iOS CI/CD](.github/workflows/ios.yml) | `push` / `pull_request` to **`main`** or **`master`**; **`workflow_dispatch`** | **SwiftLint** + **SwiftFormat** → security (Semgrep, TruffleHog, Snyk) → **in parallel**: Debug Simulator **`.app`** + unit tests (**≥80%** line coverage); both pick the **newest iOS runtime’s first available iPhone Simulator** via [`.github/scripts/ios_first_iphone_sim_udid.py`](.github/scripts/ios_first_iphone_sim_udid.py) (`platform=…,name=…,OS=…`, not a hardcoded UDID) → **archive** on **`main`/`master`** push or **manual dispatch**: install signing assets from secrets + `gym` IPA |
| [iOS code health](.github/workflows/ios-code-health.yml) | Same branches as above | **SwiftLint** + tech-debt + heuristic security reports → artifact **`ios-code-health-reports`** |
| [CodeQL Swift](.github/workflows/codeql-swift.yml) | `main` / `master` push & PR; **weekly** Monday 06:00 UTC | Swift analysis → **Security → Code scanning** (enable Code scanning on the repo) |
| [Dependabot](.github/dependabot.yml) | Weekly | Opens PRs to bump **GitHub Actions** pins |

### Reusable workflows (`workflow_call`)

These are invoked by [`.github/workflows/ios.yml`](.github/workflows/ios.yml) only (not separate top-level runs):

| File | Role |
|------|------|
| [`ios-job-lint.yml`](.github/workflows/ios-job-lint.yml) | **SwiftLint** + **SwiftFormat** (`--lint`, [`.swiftformat`](.swiftformat)) on app / test targets |
| [`ios-job-security.yml`](.github/workflows/ios-job-security.yml) | Semgrep, TruffleHog, Snyk |
| [`ios-job-simulator-artifact.yml`](.github/workflows/ios-job-simulator-artifact.yml) | Unsigned Debug Simulator **`.app`** (default artifact name: `PipelineGeneric-iphonesimulator-Debug`) |
| [`ios-job-test.yml`](.github/workflows/ios-job-test.yml) | `xcodebuild test` + **xccov** coverage gate |
| [`ios-release.yml`](.github/workflows/ios-release.yml) | `bundle exec fastlane staging_build` + optional **`upload_testflight_ipa`** |

### Manual run — archive & TestFlight

From **Actions** → **iOS CI/CD** → **Run workflow**:

- Runs the same DAG; **archive** (keychain + `gym`) always runs on manual dispatch.
- **Upload IPA to TestFlight** runs only when you enable that input (uses the App Store Connect API key secrets).

## Repository secrets

### Optional — Snyk dependency scan

| Secret | Used by |
|--------|---------|
| `SNYK_TOKEN` | `ios-job-security.yml` (Snyk only) |

_Without **`SNYK_TOKEN`**, or without a root **`Package.swift`** / **`Podfile`** (or **`Podfile.lock`**), the Snyk step is skipped (notice in the job log) so **`snyk test`** is not run on unsupported Xcode-only layouts. Add **`SNYK_TOKEN`** under **Settings → Secrets and variables → Actions** to enable Snyk when you have a supported manifest._

### Required for archive (`gym` + optional TestFlight)

| Secret | Used by |
|--------|---------|
| `DIST_CERTIFICATE_BASE64` | **Distribution** `.p12` (or `.p12` exported from Keychain) encoded with **`base64`** (no line breaks), same idea as **`IOS_DEV_CERTIFICATE_BASE64`** in the Edward Jones POC workflow |
| `DIST_CERTIFICATE_PASSWORD` | Password for that `.p12` |
| `DIST_PROFILE_BASE64` | **App Store** provisioning profile (`.mobileprovision`) **`base64`**-encoded |
| `APP_STORE_CONNECT_KEY_ID` | TestFlight upload (`upload_testflight_ipa`); still declared required by the reusable workflow |
| `APP_STORE_CONNECT_ISSUER_ID` | TestFlight upload |
| `APP_STORE_CONNECT_API_KEY` | API key **PEM contents** (plain text, not base64) |

The archive job creates a temp keychain, imports the certificate, decodes the profile, installs it as **`{UUID}.mobileprovision`**, reads **Name** / **TeamIdentifier** from the profile for manual signing, then runs **`bundle exec fastlane staging_build`**.

### Optional — signing

| Secret | Used by |
|--------|---------|
| `IOS_CODESIGN_IDENTITY` | Full **Code Signing Identity** string (e.g. `Apple Distribution: …`) when multiple distribution identities are present in the imported `.p12` |

### Optional

- **Code scanning** enabled for the repository so CodeQL results appear under **Security**.

## Local tooling

- **Ruby / Fastlane:** `bundle install` then `bundle exec fastlane staging_build` after you match CI: import the same distribution cert into your login keychain, install the App Store profile under **`~/Library/MobileDevice/Provisioning Profiles/`** as **`{UUID}.mobileprovision`**, and export **`APPLE_TEAM_ID`**, **`IOS_PROVISIONING_PROFILE_NAME`** (profile **Name** from the portal / plist), and **`APP_IDENTIFIER`** (bundle id). Or install **fastlane** via Homebrew.
- **SwiftLint:** config is [`.swiftlint.yml`](.swiftlint.yml); CI runs it in **`ios-job-lint.yml`** (main DAG) and **iOS code health** (JSON + reports artifact).
- **SwiftFormat:** config is [`.swiftformat`](.swiftformat); install with **`brew install swiftformat`**, then e.g. `swiftformat --lint PipelineGeneric/PipelineGeneric PipelineGeneric/PipelineGenericTests PipelineGeneric/PipelineGenericUITests` (same as **`ios-job-lint.yml`**).

## Layout

- **App:** [PipelineGeneric/PipelineGeneric.xcodeproj](PipelineGeneric/PipelineGeneric.xcodeproj), bundle id **`com.codeandtheory.PipelineGeneric`**.
- **Shared Xcode scheme (required for CI):** [`PipelineGeneric.xcodeproj/xcshareddata/xcschemes/PipelineGeneric.xcscheme`](PipelineGeneric/PipelineGeneric.xcodeproj/xcshareddata/xcschemes/PipelineGeneric.xcscheme) — must stay committed (do not rely only on `xcuserdata` schemes).
- **Scripts:** [`.github/scripts/`](.github/scripts/) — simulator UDID helper, code-health reports.
- **Fastlane:** [fastlane/Fastfile](fastlane/Fastfile) — lanes `staging_build`, `upload_testflight_ipa`.
- **Cursor / agent rules:** [`.cursor/rules/`](.cursor/rules/) (bootstrap, CI reference, simulator artifact runbook).

## Validate locally (optional)

```bash
# List schemes (should show PipelineGeneric)
xcodebuild -list -project PipelineGeneric/PipelineGeneric.xcodeproj

# Tests + coverage (same destination picker as CI: name + OS, not a machine-specific UDID)
DEST="$(python3 .github/scripts/ios_first_iphone_sim_udid.py)"
xcodebuild test \
  -project PipelineGeneric/PipelineGeneric.xcodeproj \
  -scheme PipelineGeneric \
  -destination "${DEST}" \
  -enableCodeCoverage YES \
  -derivedDataPath /tmp/PGDerived \
  -resultBundlePath /tmp/PGTestResults.xcresult

# Code health generators (writes under Reports/, gitignored)
python3 .github/scripts/tech_debt_scan.py
python3 .github/scripts/security_patterns_scan.py
python3 .github/scripts/codebase_health_report.py
```

Do **not** commit a nested **`ios-devops-cursor-kit/`** folder at repo root — keep a single **`.github/workflows/`** tree here; kit content should be merged once at the root.
