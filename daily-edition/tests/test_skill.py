"""The skill and plugin files agree with the Agent Skills format, with each
other, and with the repository they point to. Standard library only."""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

FOLDER = Path(__file__).resolve().parent.parent
REPO = FOLDER.parent
SKILLS = FOLDER / "skills"
PROMPT = FOLDER / "prompt.md"
DOCS = [FOLDER / "README.md", FOLDER / "PUBLISHING.md", FOLDER / "AGENTS.md", PROMPT]

# The fields claude.ai and the Skills API accept; any other fails the upload.
PORTABLE_FIELDS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
_NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
_SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
# A file path in backticks, such as `template-rendering/AGENTS.md`.
_PATH = re.compile(r"`([\w.-]+(?:/[\w.-]+)+\.(?:md|json|py))`")
# A relative Markdown link target, without its #anchor.
_LINK = re.compile(r"\]\((?!https?:|#|mailto:)([^)#\s]+)")
# A setting line in prompt.md, such as `- Stories: 8 to 15`.
_SETTING = re.compile(r"^- ([A-Z][\w ]*):", re.MULTILINE)


def frontmatter(path: Path) -> dict[str, str]:
    """Top-level `key: value` lines; nested `metadata` keys are skipped."""
    match = re.match(r"\A---\n(.*?)\n---\n", path.read_text(encoding="utf-8"), re.DOTALL)
    if not match:
        raise AssertionError(f"{path}: no frontmatter on the first line")
    fields = {}
    for line in match.group(1).splitlines():
        if line.strip() and not line.startswith((" ", "\t")):
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip()
    return fields


def skill_files() -> list[Path]:
    return sorted(SKILLS.glob("*/SKILL.md"))


class SkillTest(unittest.TestCase):
    def test_there_is_a_skill(self):
        self.assertTrue(skill_files(), f"no skills/<name>/SKILL.md in {FOLDER}")

    def test_frontmatter_is_portable(self):
        for path in skill_files():
            with self.subTest(skill=path.parent.name):
                fields = frontmatter(path)
                self.assertLessEqual(set(fields), PORTABLE_FIELDS,
                                     "claude.ai rejects other frontmatter fields")
                name = fields.get("name", "")
                self.assertEqual(name, path.parent.name, "name must match the folder")
                self.assertRegex(name, _NAME)
                self.assertLessEqual(len(name), 64)
                self.assertTrue(0 < len(fields.get("description", "")) <= 1024)
                self.assertLessEqual(len(fields.get("compatibility", "")), 500)

    def test_skill_is_short(self):
        for path in skill_files():
            with self.subTest(skill=path.parent.name):
                lines = path.read_text(encoding="utf-8").count("\n")
                self.assertLess(lines, 500, "move detail into the approaches' docs")

    def test_named_files_exist(self):
        """The repository files the agent is told to read are still there."""
        for path in skill_files() + [PROMPT]:
            for named in _PATH.findall(path.read_text(encoding="utf-8")):
                with self.subTest(file=path.name, path=named):
                    self.assertTrue((REPO / named).exists(),
                                    f"{path.name} names {named}, which isn't in the repository")

    def test_prompt_settings_are_defined(self):
        """Each setting the scheduled prompt sets is one the skill knows."""
        for path in skill_files():
            text = path.read_text(encoding="utf-8")
            settings = text.partition("## Settings")[2].partition("\n## ")[0]
            for key in _SETTING.findall(PROMPT.read_text(encoding="utf-8")):
                with self.subTest(skill=path.parent.name, setting=key):
                    self.assertIn(f"{key}:", settings,
                                  f"prompt.md sets {key}, which the skill's Settings don't define")

    def test_links_resolve(self):
        for path in skill_files() + DOCS:
            for target in _LINK.findall(path.read_text(encoding="utf-8")):
                with self.subTest(file=path.name, link=target):
                    self.assertTrue((path.parent / target).exists(),
                                    f"{path.name} links to {target}, which doesn't exist")


class PluginTest(unittest.TestCase):
    def setUp(self):
        self.plugin = json.loads((FOLDER / ".claude-plugin" / "plugin.json").read_text("utf-8"))
        self.marketplace = json.loads((REPO / ".claude-plugin" / "marketplace.json").read_text("utf-8"))

    def test_plugin_manifest(self):
        self.assertRegex(self.plugin["name"], _NAME)
        self.assertRegex(self.plugin.get("version", ""), _SEMVER)

    def test_marketplace_lists_this_folder(self):
        entries = [e for e in self.marketplace["plugins"]
                   if isinstance(e["source"], str) and (REPO / e["source"]).resolve() == FOLDER]
        self.assertEqual(len(entries), 1, "marketplace.json should list this folder once")
        self.assertEqual(entries[0]["name"], self.plugin["name"],
                         "the entry name and plugin.json's name must match")
        self.assertIn("name", self.marketplace["owner"])


if __name__ == "__main__":
    unittest.main()
