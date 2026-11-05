#!/usr/bin/env python3
"""Сборка: dist/<скилл>.zip для claude.ai и agents/<ревьюер>.md для Claude Code.

    python scripts/build.py           собрать (перезаписывает только изменившиеся файлы)
    python scripts/build.py --check   ничего не писать, только проверить, что всё актуально
                                      (код возврата 1, если ZIP или агенты устарели)
"""

from __future__ import annotations

import argparse
import io
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import (  # noqa: E402
    AGENTS_DIR,
    DIST_DIR,
    ROOT,
    expected_zip_entries,
    render_agent,
    reviewer_sources,
    skill_dirs,
)

FIXED_TIME = (1980, 1, 1, 0, 0, 0)


def make_zip(entries: dict[str, bytes]) -> bytes:
    """ZIP с фиксированными датами и порядком, чтобы пересборка без изменений давала тот же файл."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for arcname in sorted(entries):
            info = zipfile.ZipInfo(arcname, date_time=FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            info.create_system = 3  # unix: одинаковые атрибуты на любой ОС сборки
            zf.writestr(info, entries[arcname])
    return buf.getvalue()


def read_zip(path: Path) -> dict[str, bytes] | None:
    try:
        with zipfile.ZipFile(path) as zf:
            return {i.filename: zf.read(i) for i in zf.infolist() if not i.is_dir()}
    except (OSError, zipfile.BadZipFile):
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="только проверить актуальность")
    args = parser.parse_args()

    problems: list[str] = []
    written: list[str] = []

    # 1. Агенты-ревьюеры из skills/reviewers/references/*-reviewer.md
    expected_agents: dict[Path, str] = {}
    for source in reviewer_sources():
        name, text = render_agent(source)
        expected_agents[AGENTS_DIR / f"{name}.md"] = text

    if expected_agents or AGENTS_DIR.exists():
        for path, text in expected_agents.items():
            current = path.read_text(encoding="utf-8") if path.exists() else None
            if current != text:
                if args.check:
                    problems.append(f"{path.relative_to(ROOT)} устарел — запусти python scripts/build.py")
                else:
                    AGENTS_DIR.mkdir(exist_ok=True)
                    path.write_text(text, encoding="utf-8", newline="\n")
                    written.append(str(path.relative_to(ROOT)))
        for path in sorted(AGENTS_DIR.glob("*.md")) if AGENTS_DIR.exists() else []:
            if path not in expected_agents:
                if args.check:
                    problems.append(f"{path.relative_to(ROOT)} лишний: для него нет исходника в skills/reviewers/references/")
                else:
                    path.unlink()
                    written.append(f"удалён {path.relative_to(ROOT)}")

    # 2. ZIP-архивы для claude.ai
    expected_zips: dict[Path, dict[str, bytes]] = {}
    for skill_dir in skill_dirs():
        if (skill_dir / "SKILL.md").exists():
            expected_zips[DIST_DIR / f"{skill_dir.name}.zip"] = expected_zip_entries(skill_dir)

    for path, entries in expected_zips.items():
        current = read_zip(path) if path.exists() else None
        if current != entries:
            if args.check:
                problems.append(f"{path.relative_to(ROOT)} не совпадает с исходниками — запусти python scripts/build.py")
            else:
                DIST_DIR.mkdir(exist_ok=True)
                path.write_bytes(make_zip(entries))
                written.append(str(path.relative_to(ROOT)))
    for path in sorted(DIST_DIR.glob("*.zip")) if DIST_DIR.exists() else []:
        if path not in expected_zips:
            if args.check:
                problems.append(f"{path.relative_to(ROOT)} лишний: такого скилла нет")
            else:
                path.unlink()
                written.append(f"удалён {path.relative_to(ROOT)}")

    if args.check:
        if problems:
            print("Сборка устарела:")
            for p in problems:
                print(f"  - {p}")
            return 1
        print(f"OK: {len(expected_zips)} ZIP и {len(expected_agents)} агентов актуальны.")
        return 0

    if written:
        print("Обновлено:")
        for w in written:
            print(f"  - {w}")
    else:
        print("Всё уже актуально, ничего не менялось.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
