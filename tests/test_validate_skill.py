from __future__ import annotations

import importlib.util
import json
import shutil
import struct
import tempfile
import unittest
import zlib
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = PROJECT_ROOT / "scripts" / "validate_skill.py"
SPEC = importlib.util.spec_from_file_location("validate_skill", VALIDATOR_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Unable to load validate_skill.py")
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class ValidateSkillTests(unittest.TestCase):
    def copy_project(self) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temporary_directory = tempfile.TemporaryDirectory()
        destination = Path(temporary_directory.name) / "project"
        shutil.copytree(
            PROJECT_ROOT,
            destination,
            ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"),
        )
        return temporary_directory, destination

    def test_current_project_passes(self) -> None:
        self.assertEqual(VALIDATOR.validate(PROJECT_ROOT), [])

    def test_rejects_template_path_escape(self) -> None:
        temporary_directory, project = self.copy_project()
        with temporary_directory:
            manifest_path = (
                project
                / "skills"
                / "cloisonne-keepsake-design"
                / "assets"
                / "template-previews"
                / "manifest.json"
            )
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["templates"][0]["template"] = "../../../../../../etc/passwd"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            errors = VALIDATOR.validate(project)
        self.assertTrue(any("template path escapes" in error for error in errors), errors)

    def test_rejects_invalid_yaml(self) -> None:
        temporary_directory, project = self.copy_project()
        with temporary_directory:
            yaml_path = (
                project
                / "skills"
                / "cloisonne-keepsake-design"
                / "agents"
                / "openai.yaml"
            )
            yaml_path.write_text("interface: [not valid", encoding="utf-8")
            errors = VALIDATOR.validate(project)
        self.assertTrue(any("invalid YAML" in error for error in errors), errors)

    def test_rejects_unregistered_preview(self) -> None:
        temporary_directory, project = self.copy_project()
        with temporary_directory:
            previews = (
                project
                / "skills"
                / "cloisonne-keepsake-design"
                / "assets"
                / "template-previews"
            )
            shutil.copy2(previews / "01-tropical-beach-keychain.png", previews / "orphan.png")
            errors = VALIDATOR.validate(project)
        self.assertIn("unregistered preview PNG: orphan.png", errors)

    def test_rejects_unknown_style_family(self) -> None:
        temporary_directory, project = self.copy_project()
        with temporary_directory:
            manifest_path = (
                project
                / "skills"
                / "cloisonne-keepsake-design"
                / "assets"
                / "template-previews"
                / "manifest.json"
            )
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["templates"][0]["style_family"] = "unknown-style"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            errors = VALIDATOR.validate(project)
        self.assertTrue(any("unsupported style_family" in error for error in errors), errors)

    def test_rejects_unknown_output_form(self) -> None:
        temporary_directory, project = self.copy_project()
        with temporary_directory:
            manifest_path = (
                project
                / "skills"
                / "cloisonne-keepsake-design"
                / "assets"
                / "template-previews"
                / "manifest.json"
            )
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["templates"][0]["output_form"] = "unknown-output"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            errors = VALIDATOR.validate(project)
        self.assertTrue(any("unsupported output_form" in error for error in errors), errors)

    def test_requires_all_input_modes(self) -> None:
        temporary_directory, project = self.copy_project()
        with temporary_directory:
            manifest_path = (
                project
                / "skills"
                / "cloisonne-keepsake-design"
                / "assets"
                / "template-previews"
                / "manifest.json"
            )
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["input_modes"] = ["reference-image"]
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            errors = VALIDATOR.validate(project)
        self.assertIn(
            "preview manifest input_modes must contain reference-image, text-only, and hybrid",
            errors,
        )

    def test_rejects_invalid_png_crc(self) -> None:
        temporary_directory, project = self.copy_project()
        with temporary_directory:
            preview = (
                project
                / "skills"
                / "cloisonne-keepsake-design"
                / "assets"
                / "template-previews"
                / "01-tropical-beach-keychain.png"
            )
            corrupted = bytearray(preview.read_bytes())
            corrupted[-1] ^= 1
            preview.write_bytes(corrupted)
            errors = VALIDATOR.validate(project)
        self.assertTrue(any("invalid PNG CRC" in error for error in errors), errors)

    def test_rejects_png_without_image_data(self) -> None:
        temporary_directory, project = self.copy_project()
        with temporary_directory:
            preview = (
                project
                / "skills"
                / "cloisonne-keepsake-design"
                / "assets"
                / "template-previews"
                / "01-tropical-beach-keychain.png"
            )

            def chunk(chunk_type: bytes, data: bytes) -> bytes:
                crc = zlib.crc32(data, zlib.crc32(chunk_type)) & 0xFFFFFFFF
                return struct.pack(">I", len(data)) + chunk_type + data + struct.pack(">I", crc)

            ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0)
            preview.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IEND", b""))
            errors = VALIDATOR.validate(project)
        self.assertTrue(any("incomplete PNG" in error for error in errors), errors)

    def test_rejects_png_trailing_data(self) -> None:
        temporary_directory, project = self.copy_project()
        with temporary_directory:
            preview = (
                project
                / "skills"
                / "cloisonne-keepsake-design"
                / "assets"
                / "template-previews"
                / "01-tropical-beach-keychain.png"
            )
            preview.write_bytes(preview.read_bytes() + b"hidden-data")
            errors = VALIDATOR.validate(project)
        self.assertTrue(any("PNG contains trailing data" in error for error in errors), errors)

    def test_rejects_broken_markdown_link(self) -> None:
        temporary_directory, project = self.copy_project()
        with temporary_directory:
            readme = project / "README.md"
            readme.write_text(
                readme.read_text(encoding="utf-8") + "\n[broken](missing-file.md)\n",
                encoding="utf-8",
            )
            errors = VALIDATOR.validate(project)
        self.assertTrue(any("broken Markdown link" in error for error in errors), errors)

    def test_requires_text_only_input_contract(self) -> None:
        temporary_directory, project = self.copy_project()
        with temporary_directory:
            skill_path = (
                project
                / "skills"
                / "cloisonne-keepsake-design"
                / "SKILL.md"
            )
            skill_path.write_text(
                skill_path.read_text(encoding="utf-8").replace("纯文字", "文字路线"),
                encoding="utf-8",
            )
            errors = VALIDATOR.validate(project)
        self.assertIn("SKILL.md input contract must mention: 纯文字", errors)

    def test_rejects_legacy_reference_image_requirement(self) -> None:
        temporary_directory, project = self.copy_project()
        with temporary_directory:
            skill_path = (
                project
                / "skills"
                / "cloisonne-keepsake-design"
                / "SKILL.md"
            )
            skill_path.write_text(
                skill_path.read_text(encoding="utf-8")
                + "\n参考图是必需输入。\n",
                encoding="utf-8",
            )
            errors = VALIDATOR.validate(project)
        self.assertIn(
            "SKILL.md contains legacy image-only requirement: 参考图是必需输入",
            errors,
        )


if __name__ == "__main__":
    unittest.main()
