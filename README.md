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
- 
## Coverage

Implemented UI scenarios:

- `test_accessing_allowed_chatgpt_url_expects_successful_access`
- `test_accessing_blocked_gemini_url_expects_access_denied_page`
- `test_accessing_configured_blocked_url_expects_access_denied_page`
- `test_accessing_blocked_gemini_url_expects_blocked_page_visual_layout`
- `test_refreshing_blocked_gemini_url_expects_access_denied_page_to_persist`
- `test_opening_blocked_gemini_url_in_new_tab_expects_access_denied_page`
- `test_accessing_blocked_gemini_url_with_invalid_extension_api_key_expects_no_policy_enforcement`

The visual test compares the blocked modal screenshot to a committed baseline in `tests/ui/snapshots/gemini-blocked-modal.png`.

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

## Evidence Modes

`BROWSER_EVIDENCE_MODE` supports:

- `full`: always capture screenshot, trace, and video
- `failure_only`: attach evidence only when a test fails
- `screenshot_only`: attach only failure screenshots

Legacy values `always`, `on_failure`, and `off` are normalized for compatibility.

Allure attachment behavior:

- In `full` mode, passing tests also attach screenshot, trace, and video evidence.
- Because these artifacts are produced during fixture teardown, they appear in the Allure report under the `page` fixture `afters` section rather than only as top-level test attachments.

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

## Local Execution

Run the UI suite:

```powershell
python -m pytest tests\ui -m ui -q -rs --alluredir artifacts\allure-results
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
allure generate artifacts\allure-results --clean -o artifacts\allure-report
allure open artifacts\allure-report
```

## CI

The workflow runs on `push`, `pull_request`, and manual dispatch. It:

- installs dependencies
- installs Chromium for Playwright
- validates the unpacked extension
- runs the UI pytest suite
- generates an Allure HTML report
- uploads raw Allure results, the HTML report, and test artifacts

Manual dispatch supports choosing the evidence mode. If a checked-in unpacked extension is not available, CI can materialize one from `PROMPT_SECURITY_EXTENSION_ZIP_BASE64`.

## Assumptions And Tradeoffs

- The Chrome Web Store URL is not treated as a stable CI artifact source.
- The assignment uses a locally extracted unpacked extension because no real build artifact feed exists.
- The framework stays intentionally lean: one browser factory, one action layer, thin pages, and scenario-focused tests.
