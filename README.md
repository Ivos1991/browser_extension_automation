# Browser Automation SentinelOne

Production-style Pytest + Playwright framework for validating a browser extension that allows approved GenAI sites and blocks restricted ones.

## Architecture

- `config/`: environment-backed typed settings
- `constants/`: shared messages, extension paths, and evidence-mode constants
- `actions/`: reusable low-level Playwright operations
- `core/`: browser factory, logging, reporting, evidence, and visual regression utilities
- `fixtures/`: global browser lifecycle fixtures
- `pages/`: thin page objects and extension bootstrap page
- `tests/ui/`: UI scenarios and UI-specific fixtures
- `.github/workflows/`: CI checks for push and pull requests

## Coverage

Implemented UI scenarios:

- `test_accessing_allowed_chatgpt_url_expects_successful_access`
- `test_accessing_blocked_gemini_url_expects_access_denied_page`
- `test_accessing_configured_blocked_url_expects_access_denied_page`
- `test_accessing_blocked_gemini_url_expects_blocked_page_visual_layout`
- `test_refreshing_blocked_gemini_url_expects_access_denied_page_to_persist`
- `test_opening_blocked_gemini_url_in_new_tab_expects_access_denied_page`
- `test_accessing_blocked_gemini_url_with_invalid_extension_api_key_expects_no_policy_enforcement`
- `test_accessing_blocked_gemini_url_with_invalid_extension_api_domain_expects_no_policy_enforcement`
- `test_accessing_blocked_gemini_url_with_missing_extension_configuration_expects_no_policy_enforcement`

The visual test compares the blocked modal screenshot to a committed baseline in `tests/ui/snapshots/gemini-blocked-modal.png`.

Marker groups:

- `ui`: full browser-extension UI suite
- `positive`: allowed-access and enforcement-resilience scenarios
- `negative`: misconfiguration and failure-mode scenarios
- `visual`: visual regression validation

## Extension Strategy

Playwright extension automation requires an unpacked extension loaded through a persistent Chromium context.

This framework supports that directly:

- `--disable-extensions-except=<EXTENSION_PATH>`
- `--load-extension=<EXTENSION_PATH>`

For a real CI pipeline, the unpacked extension would come from a build artifact. For this assignment, the practical fallback is:

1. Install the extension once in Chrome
2. Copy the installed version folder into `extensions/prompt-security`
3. Run the framework against that unpacked payload

At runtime, the framework opens the extension popup, applies `EXTENSION_API_DOMAIN` and `EXTENSION_API_KEY`, and then executes the tests.

For reliability, extension configuration is applied through the extension's own runtime backend-refresh path instead of depending on popup field visibility. Extension log downloads also use the extension's runtime `saveLogs` message path.

## Evidence Modes

`BROWSER_EVIDENCE_MODE` supports:

- `full`: always capture screenshot, trace, video, and extension logs
- `failure_only`: attach evidence only when a test fails
- `screenshot_only`: attach only failure screenshots

Legacy values `always`, `on_failure`, and `off` are normalized for compatibility.

Allure attachment behavior:

- In `full` mode, passing tests also attach screenshot, trace, video, and extension log evidence.
- These artifacts are attached directly to the test result so they are visible on passing and failing tests without drilling into fixture teardown containers.
- Extension log capture is controlled by `EXTENSION_LOGS_ENABLED=true|false`.
- When `EXTENSION_LOGS_ENABLED=true`, the framework triggers the extension's `saveLogs` runtime flow, reads the resulting `debugLogs` buffer from extension storage, writes a local `.txt` artifact, and attaches it as `extension-logs`.
- This avoids depending on browser download events from the extension popup, which are unreliable in remote CI runners.
- The per-test `collect_all_evidence` marker still overrides the global mode and forces the full configured evidence set for that test.

## Setup

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m playwright install chromium
Copy-Item .env.example .env
```

Required `.env` values:

- `EXTENSION_PATH`
- `EXTENSION_API_DOMAIN`
- `EXTENSION_API_KEY`

Optional `.env` values:

- `EXTENSION_LOGS_ENABLED=true`
- `BROWSER_EVIDENCE_MODE=failure_only|full|screenshot_only`

## Local Execution

Run the UI suite:

```powershell
python -m pytest tests\ui -m ui -q -rs --alluredir artifacts\allure-results
```

Run only positive scenarios:

```powershell
python -m pytest tests\ui -m "ui and positive" -q -rs --alluredir artifacts\allure-results
```

Run only negative scenarios:

```powershell
python -m pytest tests\ui -m "ui and negative" -q -rs --alluredir artifacts\allure-results
```

Run only visual scenarios:

```powershell
python -m pytest tests\ui -m "ui and visual" -q -rs --alluredir artifacts\allure-results
```

Run the suite in parallel:

```powershell
python -m pytest tests\ui -m ui -n 2 -q -rs --basetemp artifacts\pytest-tmp --alluredir artifacts\allure-results
```

Run a custom marker expression:

```powershell
python -m pytest tests\ui -m "ui and positive and not visual" -q -rs --alluredir artifacts\allure-results
```

Run headed with slow motion:

```powershell
$env:HEADLESS='false'
$env:SLOW_MO_MS='700'
python -m pytest tests\ui -m ui -q -rs --alluredir artifacts\allure-results
```

Refresh the visual baseline intentionally:

```powershell
$env:UPDATE_VISUAL_BASELINES='true'
python -m pytest tests\ui -k visual -q -rs --alluredir artifacts\allure-results
```

## Allure

```powershell
python -m pytest tests\ui -m ui -q -rs --alluredir artifacts\allure-results
allure generate artifacts\allure-results --clean --single-file -o artifacts\allure-report
allure open artifacts\allure-report
```

## CI

The workflow runs on `push`, `pull_request`, and manual dispatch. It:

- installs dependencies
- installs Chromium for Playwright
- validates the unpacked extension
- runs the UI pytest suite
- generates a single-file Allure HTML report suitable for GitHub Pages publishing
- uploads raw Allure results, the HTML report, and test artifacts

Manual dispatch supports:

- `marker_selection=all_markers`: run the full `ui` suite
- `marker_selection=positive`: run `ui and positive`
- `marker_selection=negative`: run `ui and negative`
- `marker_selection=visual`: run `ui and visual`
- `marker_selection=custom`: run the expression provided in `custom_marker`
- `evidence_mode`: choose `failure_only`, `full`, or `screenshot_only`
- `parallel_run=off`: execute the suite serially
- `parallel_run=on`: execute the suite with pytest-xdist
- `worker_count`: choose `1` through `8` workers when `parallel_run=on`

Examples for remote/manual runs:

- Run all UI tests: choose `all_markers`
- Run only negative tests: choose `negative`
- Run a custom subset such as `ui and positive and not visual`: choose `custom` and enter that expression in `custom_marker`
- Run the suite in parallel: choose `parallel_run=on` and pick the desired `worker_count`
- Keep the run serial: choose `parallel_run=off`

If a checked-in unpacked extension is not available, CI can materialize one from `PROMPT_SECURITY_EXTENSION_ZIP_BASE64`.

## Assumptions And Tradeoffs

- The Chrome Web Store URL is not treated as a stable CI artifact source.
- The assignment uses a locally extracted unpacked extension because no real build artifact feed exists.
- The framework uses one persistent Chromium context per worker session and fresh pages per test. This keeps extension startup stable while remaining safe for pytest-xdist worker parallelism.
- Negative tests that mutate extension configuration explicitly restore the default configuration before the next test continues on the same worker.
- The framework stays intentionally lean: one browser factory, one action layer, thin pages, and scenario-focused tests.
