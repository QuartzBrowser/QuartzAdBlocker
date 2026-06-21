#!/usr/bin/env python3
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FILTER_ROOT = ROOT / "Filters"
RULES_PATH = ROOT / "Extension" / "rules" / "rules.json"
METADATA_PATH = ROOT / "Extension" / "rules" / "metadata.json"
MAX_RULES = 30000

FILTER_FILES = [
    "quartz/privacy.txt",
    "uBlockOrigin/assets/ublock/filters.min.txt",
    "uBlockOrigin/assets/ublock/privacy.min.txt",
    "uBlockOrigin/assets/ublock/badware.min.txt",
    "uBlockOrigin/assets/ublock/quick-fixes.min.txt",
    "uBlockOrigin/assets/ublock/unbreak.min.txt",
    "uBlockOrigin/assets/thirdparties/easylist/easylist.txt",
    "uBlockOrigin/assets/thirdparties/easylist/easyprivacy.txt",
    "uBlockOrigin/assets/thirdparties/urlhaus-filter/urlhaus-filter-online.txt",
]

COSMETIC_MARKERS = ("##", "#@#", "#?#", "#@?#", "#$#", "#%#")
RESOURCE_TYPES = {
    "document": "main_frame",
    "doc": "main_frame",
    "frame": "sub_frame",
    "subdocument": "sub_frame",
    "script": "script",
    "stylesheet": "stylesheet",
    "css": "stylesheet",
    "image": "image",
    "font": "font",
    "media": "media",
    "object": "object",
    "xmlhttprequest": "xmlhttprequest",
    "xhr": "xmlhttprequest",
    "ping": "ping",
    "websocket": "websocket",
    "other": "other",
}
UNSUPPORTED_OPTIONS = (
    "badfilter",
    "cname",
    "csp",
    "denyallow",
    "domain",
    "ehide",
    "generichide",
    "genericblock",
    "ghide",
    "header",
    "inline-font",
    "inline-script",
    "method",
    "permissions",
    "popunder",
    "popup",
    "redirect",
    "removeparam",
    "replace",
    "shide",
)
UNSUPPORTED_PATTERN_CHARS = set("[]{}()+\\")


def split_filter(line):
    if "$" not in line:
        return line, []
    pattern, options = line.split("$", 1)
    return pattern, [option.strip().lower() for option in options.split(",") if option.strip()]


def has_unsupported_option(options):
    for option in options:
        name = option[1:] if option.startswith("~") else option
        if "=" in name:
            name = name.split("=", 1)[0]
        if name in UNSUPPORTED_OPTIONS:
            return True
    return False


def make_condition(pattern, options):
    if (
        not pattern
        or any(marker in pattern for marker in COSMETIC_MARKERS)
        or pattern.startswith("/") and pattern.endswith("/")
        or any(char in pattern for char in UNSUPPORTED_PATTERN_CHARS)
        or any(char.isspace() for char in pattern)
    ):
        return None

    condition = {"urlFilter": pattern}
    included_resource_types = []
    excluded_resource_types = []

    for option in options:
        excluded = option.startswith("~")
        name = option[1:] if excluded else option
        if "=" in name:
            name = name.split("=", 1)[0]

        resource_type = RESOURCE_TYPES.get(name)
        if resource_type is None:
            continue

        if excluded:
            excluded_resource_types.append(resource_type)
        else:
            included_resource_types.append(resource_type)

    if included_resource_types:
        condition["resourceTypes"] = sorted(set(included_resource_types))
    if excluded_resource_types:
        condition["excludedResourceTypes"] = sorted(set(excluded_resource_types))

    if "third-party" in options or "3p" in options:
        condition["domainType"] = "thirdParty"
    elif "first-party" in options or "1p" in options:
        condition["domainType"] = "firstParty"

    if "match-case" in options:
        condition["isUrlFilterCaseSensitive"] = True

    return condition


def parse_rule(raw_line):
    line = raw_line.strip()
    if not line or line.startswith("!") or line.startswith("["):
        return None

    is_exception = line.startswith("@@")
    if is_exception:
        line = line[2:]

    pattern, options = split_filter(line)
    if has_unsupported_option(options):
        return None

    condition = make_condition(pattern.strip(), options)
    if condition is None:
        return None

    return {
        "priority": 2 if is_exception else 1,
        "action": {"type": "allow" if is_exception else "block"},
        "condition": condition,
    }


def main():
    RULES_PATH.parent.mkdir(parents=True, exist_ok=True)

    rules = []
    seen_signatures = set()
    parsed_lines = 0
    skipped_lines = 0

    for relative_path in FILTER_FILES:
        filter_path = FILTER_ROOT / relative_path
        with filter_path.open(encoding="utf-8") as handle:
            for line in handle:
                parsed_lines += 1
                rule = parse_rule(line)
                if rule is None:
                    skipped_lines += 1
                    continue

                signature = json.dumps(rule, sort_keys=True, separators=(",", ":"))
                if signature in seen_signatures:
                    skipped_lines += 1
                    continue

                seen_signatures.add(signature)
                rule["id"] = len(rules) + 1
                rules.append(rule)

                if len(rules) >= MAX_RULES:
                    break
        if len(rules) >= MAX_RULES:
            break

    with RULES_PATH.open("w", encoding="utf-8") as handle:
        json.dump(rules, handle, indent=2, sort_keys=True)
        handle.write("\n")

    metadata = {
        "ruleCount": len(rules),
        "parsedLineCount": parsed_lines,
        "skippedLineCount": skipped_lines,
        "maxRuleCount": MAX_RULES,
        "sourceFiles": FILTER_FILES,
    }
    with METADATA_PATH.open("w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2, sort_keys=True)
        handle.write("\n")

    print(f"Wrote {len(rules)} rules to {RULES_PATH}")


if __name__ == "__main__":
    main()

