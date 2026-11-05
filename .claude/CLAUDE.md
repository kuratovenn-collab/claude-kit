# CLAUDE.md — правила работы с этим репозиторием

Библиотека личных скиллов, которые работают и в claude.ai (загрузка ZIP), и в Claude Code (плагин из маркетплейса). Владелец — новичок, Windows 10 + PowerShell. Все тексты для пользователя — на русском.

## Структура

```
.claude-plugin/marketplace.json   маркетплейс (имя: kuratovenn-kit), один плагин «kit» с source "./"
.claude-plugin/plugin.json        манифест плагина kit (корень репозитория = корень плагина)
.claude/CLAUDE.md                 этот файл (лежит в .claude/, потому что CLAUDE.md в корне плагина валидатор считает ошибкой в режиме --strict)
skills/<имя>/SKILL.md             скиллы (+ references/ — вспомогательные файлы)
agents/<ревьюер>.md               субагенты Claude Code — ГЕНЕРИРУЮТСЯ из skills/reviewers/references/
dist/<имя>.zip                    архивы для claude.ai — ГЕНЕРИРУЮТСЯ скриптом
scripts/validate.py               проверка скиллов, агентов и манифестов
scripts/build.py                  сборка ZIP и агентов (--check — проверка, что всё актуально)
docs/                             research.md, tips.md, examples/<скилл>.md
```

## Как вносить изменения

1. Правишь `skills/<имя>/SKILL.md` или файлы в `references/`.
2. `python scripts/build.py` — пересобирает `dist/*.zip` и `agents/*.md`.
3. `python scripts/validate.py` и `claude plugin validate . --strict`.
4. Коммит. CI повторит проверки и убедится, что ZIP и агенты не устарели.

## Правила для SKILL.md (чтобы работало и в claude.ai)

- Во frontmatter только ключи: `name`, `description`, `license`, `allowed-tools`, `metadata`, `compatibility`. Поля только для Claude Code (`when_to_use`, `argument-hint`, `disable-model-invocation`, `context` …) **запрещены** — claude.ai падает на них при загрузке.
- `name` = имя папки, kebab-case, ≤64 символов, без слов claude/anthropic.
- `description` ≤1024 символов (целимся в <700), без `<` и `>`, в третьем лице: что делает + когда включать + фразы-триггеры.
- В каждой папке скилла ровно один `SKILL.md`; вспомогательные файлы — `references/*.md`, ссылки на них — один уровень вглубь.
- Тело — до 500 строк. Внутри 1–2 коротких примера хорошего результата.
- Никаких хуков, скриптов, скрытых сетевых запросов.

## Принятые решения (неоднозначные места)

| Решение | Почему |
|---|---|
| CLAUDE.md лежит в `.claude/CLAUDE.md`, а не в корне | `claude plugin validate --strict` считает CLAUDE.md в корне плагина ошибкой; Claude Code читает `.claude/CLAUDE.md` так же |
| В описаниях скиллов нет двоеточия с пробелом | Иначе YAML ломается без кавычек; валидатор это ловит |
| Ветка `claude/skills-library-b0j592`, а не `claude/skills-library` | Среда облачной сессии разрешает пушить только в эту ветку; имя отличается суффиксом, суть та же |
| Плагин называется `kit`, маркетплейс — `kuratovenn-kit` | Имена на `claude-` запрещены валидатором; короткое имя удобно: `/kit:critic` |
| Корень репозитория = корень плагина (`source: "./"`) | Требуемая структура `skills/<имя>/` сразу является структурой плагина, без копий |
| Лимит description — 1024, цель <700 | Справка claude.ai пишет 200, но API-документация, официальный валидатор Anthropic и реальные ошибки загрузки — 1024. См. docs/research.md |
| Тексты скиллов на русском | Владелец читает и поддерживает библиотеку сам; Claude одинаково хорошо следует русским инструкциям |
| Роли critic и ревьюеров описаны в `references/`, а не только в агентах | claude.ai не поддерживает агентов плагина; один и тот же текст роли используется и субагентом, и последовательным проходом |
| `agents/*.md` генерируются из `skills/reviewers/references/*.md` | Один источник правды; CI проверяет синхронность |
| ZIP-архивы коммитятся в `dist/` | Новичку проще скачать готовый файл с GitHub, чем собирать; CI проверяет, что содержимое архивов совпадает с исходниками (сравнение содержимого, а не байтов ZIP — байты зависят от версии zlib) |
| Для облачных сессий README предлагает загрузку в claude.ai или копию в `.claude/` проекта, а не `enabledPlugins` | По документации облачные сессии не устанавливают плагины из `.claude/settings.json` |
| Лицензия репозитория — MIT; чужие материалы — по их лицензиям (CREDITS.md) | Валидатор плагинов ожидает license; MIT совместима с использованными MIT/Apache-2.0 источниками |
| Прогоны цикла качества — через `claude -p --plugin-dir .` в отдельной папке, оценка — независимым субагентом | Реальный запуск скилла с его описанием, а оценщик не видел процесса создания |

## Статус

| Этап | Состояние |
|---|---|
| Изучение (docs/research.md) | готово |
| Инфраструктура (сборка, валидация, маркетплейс, CI) | готово |
| critic | готов: 2 раунда качества (docs/examples/critic.md) |
| idea-architect | готов: 2 раунда + доп. прогон (docs/examples/idea-architect.md) |
| error-doctor | готов: 2 раунда качества (docs/examples/error-doctor.md) |
| report-explainer | готов: 2 раунда качества (docs/examples/report-explainer.md) |
| handoff | готов: 2 раунда качества (docs/examples/handoff.md) |
| brainstorm | готов: 2 раунда + контрольный прогон (docs/examples/brainstorm.md) |
| fact-checker | готов: 2 раунда + контрольный прогон 3/3 (docs/examples/fact-checker.md) |
| reviewers (+ 5 агентов) | готов: 2 раунда + контрольный раунд (docs/examples/reviewers.md) |
| README, tips.md, CREDITS.md | готово |
| Финальная проверка, PR | готово: локальные проверки пройдены, PR https://github.com/kuratovenn-collab/claude-kit/pull/1, CI зелёный |
