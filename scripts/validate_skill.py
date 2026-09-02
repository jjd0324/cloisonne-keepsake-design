#!/usr/bin/env python3
"""Lightweight, dependency-free integrity checks for the published Skill."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "cloisonne-keepsake-design"
TEMPLATES = SKILL / "references" / "templates"
PREVIEWS = SKILL / "assets" / "template-previews"


def require_file(path: Path, errors: list[str]) -> None:
    if not path.is_file():
        errors.append(f"missing file: {path.relative_to(ROOT)}")


def main() -> int:
    errors: list[str] = []

    for relative_path in (
        "SKILL.md",
        "agents/openai.yaml",
        "references/product-presets.md",
        "references/style-presets.md",
        "references/quality-checklist.md",
        "references/maintenance.md",
        "references/templates/README.md",
        "assets/template-previews/manifest.json",
    ):
        require_file(SKILL / relative_path, errors)

    skill_text_path = SKILL / "SKILL.md"
    if skill_text_path.is_file():
        skill_text = skill_text_path.read_text(encoding="utf-8")
        if "name: cloisonne-keepsake-design" not in skill_text:
            errors.append("SKILL.md frontmatter must keep name: cloisonne-keepsake-design")
        if "references/templates/README.md" not in skill_text:
            errors.append("SKILL.md must link to the template library")

    manifest_path = PREVIEWS / "manifest.json"
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"invalid preview manifest JSON: {exc}")
        else:
            templates = manifest.get("templates")
            if not isinstance(templates, list) or len(templates) < 4:
                errors.append("preview manifest must contain at least four templates")
            else:
                seen_ids: set[str] = set()
                for entry in templates:
                    if not isinstance(entry, dict):
                        errors.append("each preview manifest entry must be an object")
                        continue
                    template_id = entry.get("id")
                    if not isinstance(template_id, str) or not template_id:
                        errors.append("each preview manifest entry needs a non-empty id")
                    elif template_id in seen_ids:
                        errors.append(f"duplicate template id: {template_id}")
                    else:
                        seen_ids.add(template_id)

                    preview = entry.get("preview")
                    template = entry.get("template")
                    if not isinstance(preview, str):
                        errors.append(f"{template_id or 'unknown'} has no preview path")
                    else:
                        require_file(PREVIEWS / preview, errors)
                    if not isinstance(template, str):
                        errors.append(f"{template_id or 'unknown'} has no template path")
                    else:
                        require_file((PREVIEWS / template).resolve(), errors)

    published_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in ROOT.rglob("*.md")
        if ".git" not in path.parts
    )
    for forbidden in ("/Users/", "xwechat_files", "OPENAI_API_KEY="):
        if forbidden in published_text:
            errors.append(f"published Markdown contains forbidden private marker: {forbidden}")

    if errors:
        print("Validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("Skill structure, template manifest, and privacy markers: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
