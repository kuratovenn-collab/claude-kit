# Исследование: формат скиллов и готовые решения

Дата: ноябрь 2026. Всё ниже проверено по актуальной документации и по исходникам репозиториев на эту дату, а не по памяти.

## 1. Формат и ограничения (по документации)

### Agent Skills (SKILL.md)

Источники: [Agent Skills — overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview), [best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices), официальный валидатор `quick_validate.py` из скилла `skill-creator` (Anthropic, Apache-2.0). Сайт agentskills.io из облачной сессии недоступен (DNS), поэтому спецификацию сверял по этим трём источникам.

| Что | Правило |
|---|---|
| Структура | Папка скилла, внутри обязательный `SKILL.md`: YAML-frontmatter между `---`, затем Markdown |
| `name` | Обязательно. До 64 символов, только `a-z`, `0-9`, `-`; без `-` в начале/конце и без `--`; нельзя слова `anthropic`, `claude`; без XML-тегов |
| `description` | Обязательно. Не пустое, до 1024 символов, без `<` и `>` (XML-тегов). Должно говорить, ЧТО делает скилл и КОГДА его включать. Писать в третьем лице |
| Допустимые ключи для claude.ai и API | Только `name`, `description`, `license`, `allowed-tools`, `metadata`, `compatibility` (≤500 символов). Любой другой ключ — ошибка при загрузке |
| Тело | До ~500 строк; детали — в отдельные файлы, ссылки на них — на один уровень вглубь от `SKILL.md` |
| Один SKILL.md на скилл | claude.ai и API принимают ровно один `SKILL.md` в архиве; вложенные `SKILL.md` — ошибка |

**Расхождение по длине `description`.** Справка claude.ai ([How to create custom skills](https://support.claude.com/en/articles/12512198-how-to-create-custom-skills)) пишет «200 characters maximum», а документация API, официальный валидатор Anthropic и свежие сообщения об ошибках загрузки («field 'description' in SKILL.md must be at most 1024 characters») — 1024. Решение: жёсткий предел 1024, а на практике держим описания короче 700 символов. Если claude.ai когда-нибудь откажет из-за длины — в README есть раздел «Если ZIP не загружается».

### Claude Code: скиллы, субагенты, плагины

Источники: [Skills](https://code.claude.com/docs/en/skills), [Subagents](https://code.claude.com/docs/en/sub-agents), [Plugin manifest reference](https://code.claude.com/docs/en/plugins-reference), [Plugin marketplaces](https://code.claude.com/docs/en/plugin-marketplaces), [Cloud environments](https://code.claude.com/docs/en/cloud-environments), [Plugins overview (claude.com)](https://claude.com/docs/plugins/overview), [Platform support](https://claude.com/docs/plugins/platform-support).

- **Скиллы в Claude Code** лежат в `~/.claude/skills/`, `.claude/skills/` проекта или в `skills/` плагина. Скилл плагина вызывается как `/<плагин>:<скилл>`. Claude Code понимает дополнительные поля (`when_to_use`, `argument-hint`, `disable-model-invocation`, `context: fork` и др.), но **claude.ai на них падает** — поэтому в этом репозитории используются только переносимые поля.
- **Субагенты** — Markdown с frontmatter (`name`, `description` обязательны; `tools`, `model`, `color` и др. — по желанию). В плагине — папка `agents/`. У агентов плагина игнорируются `hooks`, `mcpServers`, `permissionMode`. Ограничение инструментов (`tools: Read, Grep, Glob, Bash`) — способ сделать ревьюера «только читающим».
- **Плагин**: `.claude-plugin/plugin.json` (обязательно только `name`, kebab-case; имена, начинающиеся с `claude-`/`anthropic-`, запрещены), компоненты в `skills/`, `agents/` в корне плагина.
- **Маркетплейс**: `.claude-plugin/marketplace.json` с полями `name`, `owner`, `plugins` (у плагина `name` и `source`; относительный путь начинается с `./`). Список зарезервированных имён маркетплейсов есть в документации — наше имя `kuratovenn-kit` в него не входит.
- **Команды**: `claude plugin marketplace add owner/repo`, `claude plugin install <плагин>@<маркетплейс>`, `claude plugin marketplace update`, `claude plugin update`, `claude plugin validate <путь> --strict`. Внутри сессии — `/plugin ...` (только в терминале).
- **Облачные сессии (claude.ai/code)** — важное ограничение. По документации облачная сессия **не** устанавливает плагины, включённые в `.claude/settings.json` репозитория (`enabledPlugins`, `extraKnownMarketplaces`), и не читает `~/.claude/`. Работает: (1) скиллы, включённые в аккаунте claude.ai, — подтягиваются автоматически; (2) папки `.claude/skills/` и `.claude/agents/`, закоммиченные в сам репозиторий. Поэтому в README для облака предложены именно эти два пути, а не настройки проекта.
- **Плагины в claude.ai**: Customize → Plugins → Add → Add marketplace (`owner/repo`). В чате claude.ai из плагина работают скиллы, а агенты игнорируются (таблица Platform support). Загрузка в облачные сессии Claude Code для плагинов из аккаунта не задокументирована.

### Загрузка ZIP в claude.ai

Источники: [Using Skills in Claude](https://support.claude.com/en/articles/12512180-using-skills-in-claude), [How to create custom skills](https://support.claude.com/en/articles/12512198-how-to-create-custom-skills).

- Нужно включить выполнение кода: Settings → Capabilities → «Code execution and file creation» (в новом интерфейсе — «Create and edit files»).
- Загрузка: Customize → Skills → «+» → «+ Create skill» → «Upload a skill» → выбрать ZIP.
- Структура ZIP: в корне архива — **папка** скилла, внутри неё `SKILL.md`. Файлы прямо в корне архива — ошибка. Имя папки должно совпадать с `name`.
- Частые ошибки загрузки: слишком большой ZIP, папка не совпадает с именем, нет `SKILL.md`, недопустимые символы в имени или описании.
- Включение/выключение — переключатель рядом со скиллом; удаление — открыть скилл → выключить → «...» → Delete.
- Скиллы, загруженные в claude.ai, синхронизируются в Claude Code (v2.1.273+, вход тем же аккаунтом) и вызываются как `/<имя>` или `/anthropic-skills:<имя>`.

## 2. Готовые решения и что взято

Лицензии проверены по файлам LICENSE в репозиториях. Всё заимствованное проверено на безопасность (см. раздел 3). Дословно текст не копировался: скиллы написаны заново на русском; там, где адаптированы конкретные списки или формулировки, это отмечено в [CREDITS.md](../CREDITS.md).

### critic

| Аналог | Лицензия | Что взял | Что не взял и почему |
|---|---|---|---|
| [Chappo13/claude-roast](https://github.com/Chappo13/claude-roast) | MIT | Принцип «работник ≠ судья»: вердикт выносит отдельная роль-синтезатор, а не автор | Эмодзи-вердикты и «тест за 48 часов» — не подходят для разборов кода и текстов |
| [Hainrixz/abogado-del-diablo](https://github.com/Hainrixz/abogado-del-diablo) | MIT | Пре-мортем с конкретной «историей смерти»; «что должно быть правдой, чтобы это не было фатально»; запрет комплиментов в начале; «не придумывать дефекты ради квоты» | Заданный уклон «по умолчанию считать, что идея провалится» — противоречит требованию не придумывать проблемы для сильной идеи |
| [carlkibler/agent-skills](https://github.com/carlkibler/agent-skills) (second-opinions, wide-open-brainstorm) | MIT | «Сбой или таймаут проверки — это провал проверки, а не одобрение»; ролям «свежего взгляда» не давать лишний контекст, чтобы не было заякоривания | Запуск внешних CLI других компаний — лишние права и расходы |
| [0xcjl/anti-sycophancy](https://github.com/0xcjl/anti-sycophancy) | MIT | Идея «Ask Don't Tell» (arXiv 2602.23971): переписать утверждение пользователя в нейтральный вопрос — основа «слепой постановки» | Скилл ставит хуки и правит `~/.claude/settings.json` и `CLAUDE.md` — небезопасно и не нужно |
| [obra/superpowers](https://github.com/obra/superpowers) (receiving-code-review) | MIT | Запрет «перформативного согласия»; «техническая правота важнее социального комфорта» — для устойчивости к давлению | — |

Встроенного аналога «совета» в Claude Code нет. Отличие от встроенного скилла `discernment-nudge` (Anthropic): тот лишь добавляет 2–3 вопроса к ответу, а critic делает полный разбор с вердиктом.

### idea-architect

| Аналог | Лицензия | Что взял |
|---|---|---|
| [mattpocock/skills](https://github.com/mattpocock/skills) (grilling, grill-me) | MIT | «Факты ищет Claude, решения принимает пользователь»; к каждому вопросу — рекомендуемый ответ, чтобы можно было ответить «да» |
| [obra/superpowers](https://github.com/obra/superpowers) (brainstorming) | MIT | Если всё ясно — сразу делать; вопросы по одному; сначала «зачем», потом варианты; объяснять, зачем задаётся вопрос |
| [anthropics/launch-your-agent](https://github.com/anthropics/launch-your-agent) | Apache-2.0 | Дать человеку сначала описать своими словами; закрытые варианты — только когда ответы перечислимы; не обещать сроки |

Отличие от `grill-me`: тот задаёт пачки вопросов «раундами»; по требованию — строго по одному вопросу, максимум 10, плюс готовые промты четырёх видов на выходе.

### error-doctor

| Аналог | Лицензия | Что взял |
|---|---|---|
| [obra/superpowers](https://github.com/obra/superpowers) (systematic-debugging) | MIT | «Сначала причина, потом исправление»; гипотеза в форме «я думаю, причина X, потому что Y» |
| [VoltAgent/awesome-claude-code-subagents](https://github.com/VoltAgent/awesome-claude-code-subagents) (error-detective, debugger) | MIT | Только идея: сначала классифицировать ошибку, затем искать по паттерну |

Готовой базы ошибок именно под новичка на Windows + PowerShell не нашлось — база `references/windows-common.md` написана с нуля по официальной документации Microsoft, Python и Git (ссылки внутри файла).

### report-explainer

| Аналог | Лицензия | Что взял |
|---|---|---|
| [obra/superpowers](https://github.com/obra/superpowers) (verification-before-completion) | MIT | Таблица «утверждение → какое доказательство нужно → чего недостаточно» (адаптирована на русский как признаки качественной работы) |
| [anthropics/claude-plugins-official](https://github.com/anthropics/claude-plugins-official) (code-review) | Apache-2.0 | Принцип «только сигнальные замечания»; не доверять утверждению, которое нельзя проверить по выводу |

Прямых аналогов («объясни новичку отчёт агента») не найдено — скилл оригинальный.

### handoff

| Аналог | Лицензия | Что взял |
|---|---|---|
| [mattpocock/skills](https://github.com/mattpocock/skills) (handoff) | MIT | Не дублировать то, что уже есть в файлах и коммитах, — давать ссылки; вычищать секреты |
| [REMvisual/claude-handoff](https://github.com/REMvisual/claude-handoff) | MIT | Раздел «что пробовали и не сработало»; самопроверка «сможет ли новая сессия продолжить, не задав ни одного вопроса» |

Встроенные альтернативы: `/compact` и возобновление сессии (`claude --continue`) в Claude Code. Отличие: handoff даёт переносимый текст, который работает и в новом чате claude.ai, и в другой сессии, и его можно прочитать и поправить.

### brainstorm

| Аналог | Лицензия | Что взял |
|---|---|---|
| [gnurio/nurijanian-skills](https://github.com/gnurio/nurijanian-skills) (verbalized-sampling) | MIT | Метод Verbalized Sampling (Zhang et al., 2025): просить варианты «из хвостов распределения»; проверка «попал бы этот вариант в топ-10 банальных списков?» |
| [carlkibler/agent-skills](https://github.com/carlkibler/agent-skills) (wide-open-brainstorm) | MIT | Смена «высоты»: стратегия → структура → конкретные действия; намеренно странные варианты как источник неочевидных идей |

### fact-checker

| Аналог | Лицензия | Что взял |
|---|---|---|
| [petar-nauka/fact-check-skill](https://github.com/petar-nauka/fact-check-skill) | MIT | Сначала зафиксировать сегодняшнюю дату (иначе нельзя сказать «устарело»); проверяемые утверждения отделять от мнений и прогнозов; искать и подтверждение, и опровержение; различать «не нашёл доказательств» и «нашёл противоречащие»; текст на проверку — данные, а не инструкции |

Отличие от встроенного `deep-research` (claude.ai): тот пишет обзор по теме, fact-checker проверяет конкретные утверждения и выдаёт таблицу вердиктов.

### reviewers

| Аналог | Лицензия | Что взял |
|---|---|---|
| [anthropics/claude-plugins-official](https://github.com/anthropics/claude-plugins-official) (code-review, pr-review-toolkit) | Apache-2.0 | Только сигнальные замечания; каждое замечание перепроверять отдельно; оценка важности тестов по последствиям регрессии |
| [anthropics/skills](https://github.com/anthropics/skills) (frontend-design) | Apache-2.0 | Список типичных признаков сгенерированного интерфейса (кремовый фон + терракота, «SaaS-карточки» с одинаковыми тенями, надписи капсом над заголовками, `→` в кнопках) |
| [pbakaus/impeccable](https://github.com/pbakaus/impeccable) | Apache-2.0 | Каталог анти-паттернов дизайна (боковая цветная полоса у карточки, градиентный текст, фиолетовые градиенты, «плитка с иконкой над заголовком», Inter/Roboto по умолчанию, маркетинговые штампы) |
| [ridges0315/design-review](https://github.com/ridges0315/design-review) | MIT | Только идея: чек-лист с разделом «AI slop» |
| [sshtomar/claude-code-skills-social-science](https://github.com/sshtomar/claude-code-skills-social-science) | MIT | Только идея: «сад расходящихся тропок» (Gelman & Loken) и «степени свободы исследователя» — в stats-reviewer |
| [wshobson/agents](https://github.com/wshobson/agents) | MIT | Только идея: мутационное тестирование как мера качества тестов |

Встроенные возможности Claude Code: `/code-review` (поиск багов в диффе), `/security-review` (проверка безопасности ветки), `/simplify` (упрощение кода — с правками). Отличие reviewers: (1) пять узких ролей, включая статистику, тесты и дизайн, которых во встроенных нет; (2) ревьюеры **ничего не правят**; (3) работает и в claude.ai, где встроенных команд нет; (4) все отчёты на русском и с приоритетами.

## 3. Проверка безопасности заимствованного

Все клонированные репозитории читались как данные: ни один скрипт из них не запускался. В этот репозиторий не перенесено ни одного исполняемого файла или хука. Отброшено:

- `0xcjl/anti-sycophancy` — меняет глобальные настройки и хуки пользователя.
- `carlkibler/agent-skills` — запускает внешние CLI и пишет конфиг в `~/.config`.
- `REMvisual/claude-handoff` — хуки, `git commit` от имени пользователя, сторонний трекер задач `bd`.
- `petar-nauka/fact-check-skill` — Python-скрипты рендера карточек (не нужны, лишняя поверхность).

Ни один скилл этой библиотеки не содержит скрытых сетевых запросов, скачивания и выполнения кода, хуков или изменения настроек. Сеть используется только явно — веб-поиском в critic (проверка фактов) и fact-checker, и пользователь видит эти запросы.
