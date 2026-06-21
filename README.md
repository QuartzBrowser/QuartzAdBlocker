# Quartz Ad Blocker

Optional ad blocking for Quartz as a WebExtension package.

## Install in Quartz

1. Build or download this repository.
2. Open Quartz on macOS 15.4 or later.
3. Choose **Extensions > Install Extension...**.
4. Select the `Extension` directory in this repository, or a ZIP archive of that directory.

Quartz loads installed extensions before the first page navigation on later launches.

## What This Is

This package converts the filter assets that were formerly bundled inside Quartz into a Manifest V3 WebExtension using `declarativeNetRequest` static rules. It is intentionally separate from the browser so users can opt in.

This is not the full uBlock Origin runtime, dashboard, popup UI, dynamic filtering engine, or cosmetic filtering engine. It is a network-blocking ruleset generated from the compatible subset of the bundled filters.

## Regenerate Rules

```sh
python3 Tools/generate_rules.py
```

The generator reads `Filters/` and writes `Extension/rules/rules.json` plus `Extension/rules/metadata.json`.

