#!/usr/bin/env python3
"""Validate the published Skill package without inspecting private inputs."""

from __future__ import annotations

import json
import re
import struct
import sys
import zlib
from pathlib import Path
from urllib.parse import urlparse

import yaml


ROOT = Path(__file__).resolve().parents[1]
SKILL_NAME = "junda-visual-craft"
STYLE_FAMILIES = {
    "cloisonne-enamel",
    "minimal-paper-acrylic",
    "minimal-low-poly-editorial",
}
DISPLAY_FORMS = {"applied-carrier", "standalone-visual"}
INPUT_MODES = {"reference-image", "text-only", "hybrid"}
CURRENT_MANIFEST_VERSION = 6
MIN_TEMPLATE_COUNT = 15
PUBLIC_TEXT_SUFFIXES = {".md", ".json", ".yaml", ".yml", ".txt"}
FORBIDDEN_MARKERS = ("/" + "Users/", "xwechat_files", "OPENAI" + "_API_KEY=")
REQUIRED_INPUT_CONTRACT_MARKERS = ("纯文字", "参考图加文字")
LEGACY_IMAGE_REQUIREMENT_MARKERS = ("必须有参考图", "参考图是必需输入", "缺图时先请求上传")
TEXT_PNG_CHUNKS = {b"tEXt", b"zTXt", b"iTXt", b"eXIf"}
MAX_PNG_CHUNK_LENGTH = 64 * 1024 * 1024
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)(?:\s+[^)]*)?\)")
HTML_LINK_RE = re.compile(
    r"<(?:a|img)\b[^>]*?\b(?:href|src)\s*=\s*[\"']([^\"']+)[\"']",
    re.IGNORECASE,
)


def display(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def require_file(path: Path, root: Path, errors: list[str]) -> bool:
    if path.is_file():
        return True
    errors.append(f"missing file: {display(path, root)}")
    return False


def load_yaml(path: Path, root: Path, errors: list[str]) -> object | None:
    if not require_file(path, root, errors):
        return None
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        errors.append(f"invalid YAML: {display(path, root)}: {exc}")
    return None


def load_front_matter(path: Path, root: Path, errors: list[str]) -> object | None:
    if not require_file(path, root, errors):
        return None
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---":
        errors.append(f"SKILL.md must begin with YAML frontmatter: {display(path, root)}")
        return None
    try:
        closing_index = lines.index("---", 1)
    except ValueError:
        errors.append(f"SKILL.md has unterminated YAML frontmatter: {display(path, root)}")
        return None
    try:
        return yaml.safe_load("\n".join(lines[1:closing_index]))
    except yaml.YAMLError as exc:
        errors.append(f"invalid SKILL.md frontmatter: {display(path, root)}: {exc}")
        return None


def resolve_within(
    raw_path: object,
    *,
    base: Path,
    allowed_root: Path,
    label: str,
    root: Path,
    errors: list[str],
) -> Path | None:
    if not isinstance(raw_path, str) or not raw_path.strip():
        errors.append(f"{label} must be a non-empty relative path")
        return None
    candidate = Path(raw_path)
    if candidate.is_absolute():
        errors.append(f"{label} must not be absolute: {raw_path}")
        return None
    resolved = (base / candidate).resolve()
    if not is_within(resolved, allowed_root.resolve()):
        errors.append(f"{label} escapes {display(allowed_root, root)}: {raw_path}")
        return None
    return resolved


def extract_local_links(text: str) -> list[str]:
    targets = MARKDOWN_LINK_RE.findall(text) + HTML_LINK_RE.findall(text)
    local_targets: list[str] = []
    for target in targets:
        target = target.strip().strip("<>")
        if not target or target.startswith("#"):
            continue
        parsed = urlparse(target)
        if parsed.scheme or target.startswith("//"):
            continue
        local_targets.append(target.split("#", 1)[0].split("?", 1)[0])
    return [target for target in local_targets if target]


def validate_markdown_links(root: Path, errors: list[str]) -> None:
    for markdown_path in root.rglob("*.md"):
        if ".git" in markdown_path.parts:
            continue
        text = markdown_path.read_text(encoding="utf-8")
        for target in extract_local_links(text):
            candidate = Path(target)
            if candidate.is_absolute():
                errors.append(
                    f"absolute Markdown link in {display(markdown_path, root)}: {target}"
                )
                continue
            resolved = (markdown_path.parent / candidate).resolve()
            if not is_within(resolved, root.resolve()):
                errors.append(
                    f"Markdown link escapes repository in {display(markdown_path, root)}: {target}"
                )
            elif not resolved.is_file():
                errors.append(
                    f"broken Markdown link in {display(markdown_path, root)}: {target}"
                )


def validate_png(path: Path, root: Path, errors: list[str]) -> None:
    try:
        with path.open("rb") as handle:
            if handle.read(8) != b"\x89PNG\r\n\x1a\n":
                errors.append(f"invalid PNG signature: {display(path, root)}")
                return
            saw_ihdr = False
            saw_idat = False
            saw_iend = False
            while True:
                header = handle.read(8)
                if not header:
                    break
                if len(header) != 8:
                    errors.append(f"truncated PNG chunk header: {display(path, root)}")
                    return
                length, chunk_type = struct.unpack(">I4s", header)
                if length > MAX_PNG_CHUNK_LENGTH:
                    errors.append(f"PNG chunk exceeds size limit: {display(path, root)}")
                    return
                data = handle.read(length)
                crc = handle.read(4)
                if len(data) != length or len(crc) != 4:
                    errors.append(f"truncated PNG chunk: {display(path, root)}")
                    return
                expected_crc = struct.unpack(">I", crc)[0]
                actual_crc = zlib.crc32(data, zlib.crc32(chunk_type)) & 0xFFFFFFFF
                if actual_crc != expected_crc:
                    errors.append(f"invalid PNG CRC: {display(path, root)}")
                    return
                if not saw_ihdr and chunk_type != b"IHDR":
                    errors.append(f"PNG must begin with IHDR: {display(path, root)}")
                    return
                if chunk_type == b"IHDR":
                    if saw_ihdr or len(data) != 13:
                        errors.append(f"invalid PNG IHDR: {display(path, root)}")
                        return
                    width, height = struct.unpack(">II", data[:8])
                    if not width or not height:
                        errors.append(f"PNG must have non-zero dimensions: {display(path, root)}")
                        return
                    saw_ihdr = True
                if chunk_type == b"IDAT":
                    saw_idat = True
                if chunk_type in TEXT_PNG_CHUNKS:
                    errors.append(
                        f"PNG contains disallowed metadata chunk {chunk_type.decode()}: {display(path, root)}"
                    )
                if chunk_type == b"IEND":
                    if length != 0:
                        errors.append(f"invalid PNG IEND: {display(path, root)}")
                        return
                    saw_iend = True
                    if handle.read(1):
                        errors.append(f"PNG contains trailing data: {display(path, root)}")
                    break
            if not saw_ihdr or not saw_idat or not saw_iend:
                errors.append(f"incomplete PNG: {display(path, root)}")
    except OSError as exc:
        errors.append(f"cannot read PNG {display(path, root)}: {exc}")


def validate_manifest(skill: Path, root: Path, errors: list[str]) -> None:
    templates_root = skill / "references" / "templates"
    previews_root = skill / "assets" / "template-previews"
    manifest_path = previews_root / "manifest.json"
    if not require_file(manifest_path, root, errors):
        return
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"invalid preview manifest JSON: {exc}")
        return
    if not isinstance(manifest, dict):
        errors.append("preview manifest must be a JSON object")
        return
    if manifest.get("version") != CURRENT_MANIFEST_VERSION:
        errors.append(
            f"preview manifest version must be {CURRENT_MANIFEST_VERSION}"
        )
    input_modes = manifest.get("input_modes")
    if (
        not isinstance(input_modes, list)
        or len(input_modes) != len(INPUT_MODES)
        or not all(isinstance(mode, str) for mode in input_modes)
        or set(input_modes) != INPUT_MODES
    ):
        errors.append(
            "preview manifest input_modes must contain reference-image, text-only, and hybrid"
        )
    entries = manifest.get("templates")
    if not isinstance(entries, list):
        errors.append("preview manifest templates must be a list")
        return
    if len(entries) < MIN_TEMPLATE_COUNT:
        errors.append(
            f"preview manifest must contain at least {MIN_TEMPLATE_COUNT} templates"
        )

    seen_ids: set[str] = set()
    seen_style_families: set[str] = set()
    registered_previews: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            errors.append("each preview manifest entry must be an object")
            continue
        template_id = entry.get("id")
        if not isinstance(template_id, str) or not template_id:
            errors.append("each preview manifest entry needs a non-empty id")
            template_id = "unknown"
        elif template_id in seen_ids:
            errors.append(f"duplicate template id: {template_id}")
        else:
            seen_ids.add(template_id)

        style_family = entry.get("style_family")
        if style_family not in STYLE_FAMILIES:
            errors.append(
                f"{template_id} has unsupported style_family: {style_family}"
            )
        else:
            seen_style_families.add(style_family)
        display_form = entry.get("display_form")
        if display_form not in DISPLAY_FORMS:
            errors.append(
                f"{template_id} has unsupported display_form: {display_form}"
            )

        preview_path = resolve_within(
            entry.get("preview"),
            base=previews_root,
            allowed_root=previews_root,
            label=f"{template_id} preview path",
            root=root,
            errors=errors,
        )
        if preview_path is not None:
            if preview_path.suffix.lower() != ".png":
                errors.append(f"{template_id} preview must be a PNG: {entry.get('preview')}")
            elif not require_file(preview_path, root, errors):
                pass
            else:
                relative_preview = preview_path.relative_to(previews_root).as_posix()
                if relative_preview in registered_previews:
                    errors.append(f"duplicate preview path: {relative_preview}")
                registered_previews.add(relative_preview)
                validate_png(preview_path, root, errors)

        template_path = resolve_within(
            entry.get("template"),
            base=previews_root,
            allowed_root=templates_root,
            label=f"{template_id} template path",
            root=root,
            errors=errors,
        )
        if template_path is not None:
            require_file(template_path, root, errors)

    actual_previews = {
        path.relative_to(previews_root).as_posix() for path in previews_root.rglob("*.png")
    }
    for preview in sorted(actual_previews - registered_previews):
        errors.append(f"unregistered preview PNG: {preview}")
    for preview in sorted(registered_previews - actual_previews):
        errors.append(f"manifest preview is missing from disk: {preview}")

    missing_style_families = STYLE_FAMILIES - seen_style_families
    if missing_style_families:
        errors.append(
            "preview manifest is missing style families: "
            + ", ".join(sorted(missing_style_families))
        )

    index_path = templates_root / "README.md"
    if not require_file(index_path, root, errors):
        return
    indexed_templates: set[Path] = set()
    for target in extract_local_links(index_path.read_text(encoding="utf-8")):
        resolved = (index_path.parent / target).resolve()
        if is_within(resolved, templates_root.resolve()) and resolved.suffix == ".md":
            indexed_templates.add(resolved)
    for template_path in templates_root.rglob("*.md"):
        if template_path.name == "README.md":
            continue
        if template_path.resolve() not in indexed_templates:
            errors.append(
                f"template is missing from template index: {display(template_path, root)}"
            )


def load_jsonl(path: Path, root: Path, errors: list[str]) -> list[object]:
    if not require_file(path, root, errors):
        return []
    records: list[object] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as exc:
            errors.append(f"invalid JSONL in {display(path, root)}:{line_number}: {exc}")
    return records


def validate_evals(root: Path, errors: list[str]) -> None:
    evals_root = root / "evals" / "public"
    routing_records = load_jsonl(evals_root / "routing-cases.jsonl", root, errors)
    behavior_records = load_jsonl(evals_root / "behavior-cases.jsonl", root, errors)

    positive_count = 0
    negative_count = 0
    routing_ids: set[str] = set()
    for record in routing_records:
        if not isinstance(record, dict):
            errors.append("routing case must be a JSON object")
            continue
        case_id = record.get("id")
        if not isinstance(case_id, str) or not case_id:
            errors.append("routing case needs a non-empty id")
        elif case_id in routing_ids:
            errors.append(f"duplicate routing case id: {case_id}")
        else:
            routing_ids.add(case_id)
        if not isinstance(record.get("prompt"), str) or not isinstance(record.get("reason"), str):
            errors.append(f"routing case {case_id or 'unknown'} needs prompt and reason strings")
        intent = record.get("intent")
        if intent == "should_trigger":
            positive_count += 1
        elif intent == "should_not_trigger":
            negative_count += 1
        else:
            errors.append(f"routing case {case_id or 'unknown'} has invalid intent: {intent}")
    if positive_count < 12 or negative_count < 8:
        errors.append("routing cases need at least 12 trigger and 8 non-trigger examples")

    behavior_ids: set[str] = set()
    for record in behavior_records:
        if not isinstance(record, dict):
            errors.append("behavior case must be a JSON object")
            continue
        case_id = record.get("id")
        if not isinstance(case_id, str) or not case_id:
            errors.append("behavior case needs a non-empty id")
        elif case_id in behavior_ids:
            errors.append(f"duplicate behavior case id: {case_id}")
        else:
            behavior_ids.add(case_id)
        if not isinstance(record.get("request"), str):
            errors.append(f"behavior case {case_id or 'unknown'} needs a request string")
        for field in ("must", "must_not"):
            values = record.get(field)
            if not isinstance(values, list) or not values or not all(
                isinstance(value, str) and value for value in values
            ):
                errors.append(f"behavior case {case_id or 'unknown'} needs non-empty {field} strings")
    if len(behavior_ids) < 8:
        errors.append("behavior cases need at least eight examples")


def validate_public_text(root: Path, errors: list[str]) -> None:
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in PUBLIC_TEXT_SUFFIXES:
            continue
        relative = path.relative_to(root)
        if ".git" in relative.parts:
            continue
        if relative.parts[:1] == ("evals",) and relative.parts[:2] != ("evals", "public"):
            continue
        text = path.read_text(encoding="utf-8")
        for marker in FORBIDDEN_MARKERS:
            if marker in text:
                errors.append(
                    f"published text contains forbidden private marker {marker}: {relative.as_posix()}"
                )


def validate_input_contract(skill: Path, root: Path, errors: list[str]) -> None:
    skill_path = skill / "SKILL.md"
    if not require_file(skill_path, root, errors):
        return
    text = skill_path.read_text(encoding="utf-8")
    for marker in REQUIRED_INPUT_CONTRACT_MARKERS:
        if marker not in text:
            errors.append(f"SKILL.md input contract must mention: {marker}")
    for marker in LEGACY_IMAGE_REQUIREMENT_MARKERS:
        if marker in text:
            errors.append(f"SKILL.md contains legacy image-only requirement: {marker}")


def validate(root: Path = ROOT) -> list[str]:
    root = root.resolve()
    skill = root / "skills" / SKILL_NAME
    errors: list[str] = []

    for relative_path in (
        "SKILL.md",
        "agents/openai.yaml",
        "references/product-presets.md",
        "references/style-presets.md",
        "references/styles/cloisonne-enamel.md",
        "references/styles/minimal-paper-acrylic.md",
        "references/styles/minimal-low-poly-editorial.md",
        "references/output-formats.md",
        "references/composition-complexity.md",
        "references/delivery-format.md",
        "references/quality-checklist.md",
        "references/maintenance.md",
        "references/templates/README.md",
        "assets/template-previews/manifest.json",
    ):
        require_file(skill / relative_path, root, errors)
    for relative_path in (
        "README.md",
        "LICENSE",
        "ASSETS-LICENSE.md",
        "evals/public/README.md",
        "evals/public/routing-cases.jsonl",
        "evals/public/behavior-cases.jsonl",
        "evals/public/visual-rubric.md",
    ):
        require_file(root / relative_path, root, errors)

    front_matter = load_front_matter(skill / "SKILL.md", root, errors)
    if isinstance(front_matter, dict):
        if front_matter.get("name") != SKILL_NAME:
            errors.append(f"SKILL.md frontmatter must keep name: {SKILL_NAME}")
        if not isinstance(front_matter.get("description"), str) or not front_matter["description"].strip():
            errors.append("SKILL.md frontmatter needs a non-empty description")

    openai_config = load_yaml(skill / "agents" / "openai.yaml", root, errors)
    if isinstance(openai_config, dict):
        interface = openai_config.get("interface")
        if not isinstance(interface, dict):
            errors.append("openai.yaml needs an interface object")
        else:
            for field in ("display_name", "short_description", "default_prompt"):
                if not isinstance(interface.get(field), str) or not interface[field].strip():
                    errors.append(f"openai.yaml interface needs a non-empty {field}")
            default_prompt = interface.get("default_prompt")
            if isinstance(default_prompt, str) and f"${SKILL_NAME}" not in default_prompt:
                errors.append(f"openai.yaml default_prompt must mention ${SKILL_NAME}")
        policy = openai_config.get("policy")
        if not isinstance(policy, dict) or not isinstance(policy.get("allow_implicit_invocation"), bool):
            errors.append("openai.yaml policy needs boolean allow_implicit_invocation")

    validate_manifest(skill, root, errors)
    validate_markdown_links(root, errors)
    validate_evals(root, errors)
    validate_input_contract(skill, root, errors)
    validate_public_text(root, errors)
    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("Validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("Skill package, public evals, links, PNGs, and privacy markers: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
