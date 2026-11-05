"""Общие функции для validate.py и build.py."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"
AGENTS_DIR = ROOT / "agents"
DIST_DIR = ROOT / "dist"
REVIEWERS_REF_DIR = SKILLS_DIR / "reviewers" / "references"

# Файлы, которые не попадают в ZIP.
JUNK_NAMES = {".DS_Store", "Thumbs.db", "desktop.ini"}
JUNK_DIRS = {"__pycache__", "node_modules", ".git"}

FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n?(.*)\Z", re.DOTALL)


def split_frontmatter(text: str) -> tuple[dict, str]:
    """Возвращает (frontmatter, тело). Бросает ValueError, если frontmatter нет или он кривой."""
    match = FRONTMATTER_RE.match(text)
    if not match:
        raise ValueError("нет YAML-frontmatter между строками '---' в самом начале файла")
    try:
        data = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        raise ValueError(f"YAML во frontmatter не разбирается: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("frontmatter должен быть словарём ключ: значение")
    return data, match.group(2)


def skill_dirs() -> list[Path]:
    if not SKILLS_DIR.is_dir():
        return []
    return sorted(p for p in SKILLS_DIR.iterdir() if p.is_dir() and not p.name.startswith("."))


def skill_files(skill_dir: Path) -> list[Path]:
    """Файлы скилла, которые попадают в ZIP, в стабильном порядке."""
    files = []
    for path in sorted(skill_dir.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(skill_dir)
        if any(part in JUNK_DIRS for part in rel.parts) or path.name in JUNK_NAMES:
            continue
        if path.suffix in {".pyc"}:
            continue
        files.append(path)
    return files


def expected_zip_entries(skill_dir: Path) -> dict[str, bytes]:
    """Что должно лежать в dist/<имя>.zip: путь внутри архива -> байты."""
    name = skill_dir.name
    return {
        f"{name}/{path.relative_to(skill_dir).as_posix()}": path.read_bytes()
        for path in skill_files(skill_dir)
    }


def reviewer_sources() -> list[Path]:
    if not REVIEWERS_REF_DIR.is_dir():
        return []
    return sorted(REVIEWERS_REF_DIR.glob("*-reviewer.md"))


AGENT_TOOLS = "Read, Grep, Glob, Bash"
AGENT_COLORS = {
    "code-reviewer": "blue",
    "test-reviewer": "green",
    "stats-reviewer": "purple",
    "privacy-security-reviewer": "red",
    "design-reviewer": "pink",
}


def render_agent(source: Path) -> tuple[str, str]:
    """Собирает текст субагента из references/<имя>-reviewer.md. Возвращает (имя, текст)."""
    meta, body = split_frontmatter(source.read_text(encoding="utf-8"))
    name = meta["name"]
    front = {
        "name": name,
        "description": meta["description"],
        "tools": AGENT_TOOLS,
        "model": "inherit",
        "color": AGENT_COLORS.get(name, "cyan"),
    }
    header = yaml.safe_dump(front, allow_unicode=True, sort_keys=False, width=10000).strip()
    note = (
        "<!-- Файл сгенерирован scripts/build.py из "
        f"skills/reviewers/references/{source.name}. Правь исходник, а не этот файл. -->"
    )
    return name, f"---\n{header}\n---\n\n{note}\n\n{body.lstrip()}"
