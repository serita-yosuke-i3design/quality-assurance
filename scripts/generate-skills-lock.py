#!/usr/bin/env python3
"""skill-catalog.json から qa-skills.lock を生成する。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

QA_REPO = Path(__file__).resolve().parents[1]
CATALOG = QA_REPO / "skill-governance" / "skill-catalog.json"
PLATFORM_REPO = "git@github.com:serita-yosuke-i3design/quality-assurance.git"


def load_catalog() -> dict:
    return json.loads(CATALOG.read_text(encoding="utf-8"))


def select_skills(catalog: dict, include_beta: bool) -> dict[str, str]:
    allowed = {"distributed"}
    if include_beta:
        allowed.add("beta")
    out: dict[str, str] = {}
    for name, meta in catalog["skills"].items():
        if meta["tier"] in allowed:
            out[name] = meta["version"]
    return dict(sorted(out.items()))


def render_lock(skills: dict[str, str], profile: str = "default") -> str:
    lines = [
        "# Generated from skill-governance/skill-catalog.json",
        "# Regenerate: scripts/generate-skills-lock.py",
        "",
        "platform: quality-assurance",
        f"platform_repo: {PLATFORM_REPO}",
        "",
        "skills:",
    ]
    for name, version in skills.items():
        lines.append(f'  {name}: "{version}"')
    lines.extend(
        [
            "",
            "synced_at: null",
            "qa_repo_ref: main",
            f"profile: {profile}",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate qa-skills.lock from skill catalog")
    parser.add_argument(
        "--include-beta",
        action="store_true",
        help="Include beta tier skills (default: distributed only)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Write lock file (default: stdout)",
    )
    parser.add_argument("--profile", default="default")
    args = parser.parse_args()

    catalog = load_catalog()
    skills = select_skills(catalog, args.include_beta)
    if not skills:
        print("No skills matched tier filter", file=sys.stderr)
        return 1

    content = render_lock(skills, args.profile)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(content, encoding="utf-8")
    else:
        sys.stdout.write(content)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
