#!/usr/bin/env python3
"""Проверка репозитория: скиллы, агенты, манифесты плагина и маркетплейса, ZIP-архивы.

    python scripts/validate.py

Правила для SKILL.md взяты из документации Agent Skills и официального валидатора
Anthropic (skill-creator/quick_validate.py), чтобы файл загружался в claude.ai без ошибок.
Код возврата 1 — есть ошибки. Предупреждения ошибкой не считаются.
"""

from __future__ import annotations

import json
import re
import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import AGENTS_DIR, DIST_DIR, ROOT, skill_dirs, split_frontmatter  # noqa: E402

# Ключи, которые принимает claude.ai / Skills API. Остальные — ошибка при загрузке.
ALLOWED_SKILL_KEYS = {"name", "description", "license", "allowed-tools", "metadata", "compatibility"}
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
RESERVED_WORDS = ("anthropic", "claude")
DESCRIPTION_MAX = 1024
DESCRIPTION_SOFT_MAX = 700
BODY_MAX_LINES = 500
ALLOWED_SKILL_SUFFIXES = {".md", ".txt"}

AGENT_ALLOWED_TOOLS = {"Read", "Grep", "Glob", "Bash"}

errors: list[str] = []
warnings: list[str] = []


def err(where: str, msg: str) -> None:
    errors.append(f"{where}: {msg}")


def warn(where: str, msg: str) -> None:
    warnings.append(f"{where}: {msg}")


def rel(path: Path, base: Path = ROOT) -> str:
    try:
        return path.relative_to(base).as_posix()
    except ValueError:
        return path.as_posix()


def check_skill(skill_dir: Path, label: str | None = None) -> str | None:
    """Проверяет одну папку скилла. Возвращает name из frontmatter (или None)."""
    where = label or rel(skill_dir)
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        err(where, "нет файла SKILL.md (имя важно: заглавными буквами)")
        return None

    nested = [p for p in skill_dir.rglob("SKILL.md") if p != skill_md]
    if nested:
        err(where, f"вложенные SKILL.md запрещены (claude.ai принимает ровно один): {[rel(p, skill_dir) for p in nested]}")

    for path in skill_dir.rglob("*"):
        if path.is_file() and path.suffix.lower() not in ALLOWED_SKILL_SUFFIXES:
            err(where, f"неожиданный файл {rel(path, skill_dir)}: в скиллах этой библиотеки только .md/.txt, без скриптов")

    text = skill_md.read_text(encoding="utf-8")
    try:
        meta, body = split_frontmatter(text)
    except ValueError as exc:
        err(where, str(exc))
        return None

    extra = set(meta) - ALLOWED_SKILL_KEYS
    if extra:
        err(where, f"недопустимые ключи во frontmatter {sorted(extra)}; claude.ai принимает только {sorted(ALLOWED_SKILL_KEYS)}")

    name = meta.get("name")
    if not isinstance(name, str) or not name.strip():
        err(where, "нет поля name")
        name = None
    else:
        if not NAME_RE.match(name):
            err(where, f"name '{name}': только строчные латинские буквы, цифры и одиночные дефисы")
        if len(name) > 64:
            err(where, f"name длиннее 64 символов ({len(name)})")
        for word in RESERVED_WORDS:
            if word in name:
                err(where, f"name содержит зарезервированное слово '{word}'")
        if name != skill_dir.name:
            err(where, f"name '{name}' не совпадает с именем папки '{skill_dir.name}' — claude.ai откажет в загрузке")

    desc = meta.get("description")
    if not isinstance(desc, str) or not desc.strip():
        err(where, "нет поля description (по нему Claude решает, когда включать скилл)")
    else:
        d = desc.strip()
        if len(d) > DESCRIPTION_MAX:
            err(where, f"description длиннее {DESCRIPTION_MAX} символов ({len(d)})")
        elif len(d) > DESCRIPTION_SOFT_MAX:
            warn(where, f"description {len(d)} символов — лучше короче {DESCRIPTION_SOFT_MAX}")
        if "<" in d or ">" in d:
            err(where, "в description нельзя символы < и > (claude.ai считает их XML-тегами)")

    comp = meta.get("compatibility")
    if comp is not None and (not isinstance(comp, str) or len(comp) > 500):
        err(where, "compatibility должен быть строкой до 500 символов")

    lines = body.count("\n") + 1
    if lines > BODY_MAX_LINES:
        err(where, f"тело SKILL.md {lines} строк — больше {BODY_MAX_LINES}; вынеси детали в references/")

    # Ссылки на вспомогательные файлы: каждая должна существовать, каждый файл — упоминаться.
    mentioned = set(re.findall(r"references/[A-Za-z0-9_.\-]+\.(?:md|txt)", text))
    for ref in sorted(mentioned):
        if not (skill_dir / ref).is_file():
            err(where, f"SKILL.md ссылается на {ref}, но такого файла нет")
    ref_dir = skill_dir / "references"
    if ref_dir.is_dir():
        for path in sorted(ref_dir.rglob("*")):
            if path.is_file() and rel(path, skill_dir) not in mentioned:
                warn(where, f"{rel(path, skill_dir)} нигде не упомянут в SKILL.md — Claude его не найдёт")
    return name


def check_agents() -> None:
    if not AGENTS_DIR.is_dir():
        return
    for path in sorted(AGENTS_DIR.glob("*.md")):
        where = rel(path)
        try:
            meta, body = split_frontmatter(path.read_text(encoding="utf-8"))
        except ValueError as exc:
            err(where, str(exc))
            continue
        name = meta.get("name")
        if not isinstance(name, str) or not name:
            err(where, "нет name")
        elif ":" in name or name.startswith("-"):
            err(where, "name не может содержать ':' и начинаться с '-'")
        elif name != path.stem:
            err(where, f"name '{name}' не совпадает с именем файла")
        if not isinstance(meta.get("description"), str) or not meta["description"].strip():
            err(where, "нет description")
        tools = {t.strip() for t in str(meta.get("tools", "")).split(",") if t.strip()}
        if not tools:
            err(where, "у ревьюера должен быть явный список tools (иначе он унаследует право править файлы)")
        elif tools - AGENT_ALLOWED_TOOLS:
            err(where, f"ревьюеры только читают; лишние инструменты: {sorted(tools - AGENT_ALLOWED_TOOLS)}")
        if not body.strip():
            err(where, "пустое тело (системный промт агента)")


def load_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        err(rel(path), "файл не найден")
    except json.JSONDecodeError as exc:
        err(rel(path), f"некорректный JSON: {exc}")
    return None


def check_manifests() -> None:
    plugin = load_json(ROOT / ".claude-plugin" / "plugin.json")
    market = load_json(ROOT / ".claude-plugin" / "marketplace.json")
    if plugin:
        name = plugin.get("name", "")
        if not NAME_RE.match(name or ""):
            err("plugin.json", f"name '{name}' должен быть в kebab-case")
        if re.match(r"^(claude|anthropic|anthropics|cc-plugin)(-|$)", name or ""):
            err("plugin.json", "имена на claude-/anthropic- запрещены")
        if not plugin.get("version"):
            warn("plugin.json", "нет version — обновления плагина не будут видны")
    if market:
        for key in ("name", "owner", "plugins"):
            if key not in market:
                err("marketplace.json", f"нет обязательного поля {key}")
        if not isinstance(market.get("owner"), dict) or not market["owner"].get("name"):
            err("marketplace.json", "owner.name обязателен")
        names = []
        for i, entry in enumerate(market.get("plugins", [])):
            if not entry.get("name") or not entry.get("source"):
                err("marketplace.json", f"plugins[{i}]: нужны name и source")
            src = entry.get("source")
            if isinstance(src, str) and not src.startswith("./"):
                err("marketplace.json", f"plugins[{i}].source: относительный путь должен начинаться с ./")
            names.append(entry.get("name"))
        if plugin and plugin.get("name") not in names:
            err("marketplace.json", f"плагин '{plugin.get('name')}' из plugin.json не указан в маркетплейсе")


def safe_extract(zf: zipfile.ZipFile, dest: Path) -> None:
    for info in zf.infolist():
        target = (dest / info.filename).resolve()
        if not str(target).startswith(str(dest.resolve())):
            raise ValueError(f"путь выходит за пределы архива: {info.filename}")
    zf.extractall(dest)


def check_zips(skill_names: set[str]) -> None:
    if not DIST_DIR.is_dir():
        if skill_names:
            err("dist/", "нет папки с архивами — запусти python scripts/build.py")
        return
    for name in sorted(skill_names):
        if not (DIST_DIR / f"{name}.zip").is_file():
            err("dist/", f"нет архива {name}.zip — запусти python scripts/build.py")
    for path in sorted(DIST_DIR.glob("*.zip")):
        where = rel(path)
        expected = path.stem
        try:
            with zipfile.ZipFile(path) as zf:
                bad = zf.testzip()
                if bad:
                    err(where, f"повреждён файл внутри архива: {bad}")
                    continue
                top = {n.split("/", 1)[0] for n in zf.namelist()}
                if top != {expected}:
                    err(where, f"в корне архива должна быть ровно одна папка '{expected}', а там: {sorted(top)}")
                    continue
                with tempfile.TemporaryDirectory() as tmp:
                    safe_extract(zf, Path(tmp))
                    got = check_skill(Path(tmp) / expected, label=f"{where} (после распаковки)")
                    if got and got != expected:
                        err(where, f"имя архива '{expected}' не совпадает с name '{got}'")
        except zipfile.BadZipFile:
            err(where, "это не ZIP-архив")


def check_readme(skill_names: set[str]) -> None:
    readme = ROOT / "README.md"
    if not readme.is_file():
        err("README.md", "нет README")
        return
    text = readme.read_text(encoding="utf-8")
    for name in sorted(skill_names):
        if f"`{name}`" not in text and f"**{name}**" not in text:
            warn("README.md", f"скилл {name} не упомянут в таблице README")


def main() -> int:
    names = set()
    for skill_dir in skill_dirs():
        got = check_skill(skill_dir)
        if got:
            names.add(got)
    check_agents()
    check_manifests()
    check_zips({d.name for d in skill_dirs()})
    check_readme(names)

    for w in warnings:
        print(f"ПРЕДУПРЕЖДЕНИЕ  {w}")
    for e in errors:
        print(f"ОШИБКА          {e}")
    n_agents = len(list(AGENTS_DIR.glob('*.md'))) if AGENTS_DIR.is_dir() else 0
    summary = f"скиллов: {len(skill_dirs())}, агентов: {n_agents}, ошибок: {len(errors)}, предупреждений: {len(warnings)}"
    print(("ПРОВАЛ — " if errors else "OK — ") + summary)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
