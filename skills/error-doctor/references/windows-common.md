# База частых проблем: Windows 10 + PowerShell

Каждая запись: симптомы (как выглядит ошибка), причина, исправление, проверка, профилактика, официальный источник. Тексты ошибок даны на английском и русском — Windows и программы бывают в обеих локализациях.

Общее правило: после установки программ и изменения PATH **закрой и заново открой** окно PowerShell (и VS Code, если терминал в нём) — старые окна не видят изменений.

В PowerShell `where` — это не поиск программ, а другая команда. Чтобы узнать, где лежит программа, используй `where.exe python` или `Get-Command python`.

## Содержание

1. Python не найден или открывается Microsoft Store
2. Git не найден
3. PATH: программа установлена, но не находится
4. venv: создание, активация, Activate.ps1
5. ExecutionPolicy: «выполнение сценариев отключено»
6. Защита папки «Документы» мешает git clone
7. Ошибки прав на других дисках (D:, флешки, внешние диски)
8. venv сломался после переноса или переименования папки
9. При копировании проекта потерялась скрытая папка .git
10. Git: «detected dubious ownership»
11. Конфликты при git pull
12. ModuleNotFoundError: библиотека установлена, но не находится

---

## 1. Python не найден или открывается Microsoft Store

**Симптомы**
- `python : The term 'python' is not recognized as the name of a cmdlet…`
- «python : Имя "python" не распознано как имя командлета, функции, файла сценария или выполняемой программы»
- Команда `python` открывает Microsoft Store или молча ничего не делает.
- `pip` не найден.

**Причины**
1. Python не установлен.
2. Python установлен, но его папка не в PATH (в старом установщике не отмечена галочка «Add python.exe to PATH»).
3. Срабатывает «псевдоним» Windows: заглушка `python.exe`, которая открывает Store.

**Диагностика**
```powershell
Get-Command python, py -ErrorAction SilentlyContinue | Format-Table Name, Source
```
Если `Source` ведёт в `...\Microsoft\WindowsApps\python.exe`, а Python не устанавливался — это заглушка Store.

**Исправление**
- Рекомендуемый сейчас способ — **Python install manager** с [python.org/downloads](https://www.python.org/downloads/) или из Microsoft Store (это одна и та же программа). После установки в новом окне PowerShell:
  ```powershell
  py install 3.14
  ```
  Затем `python` и `py` запускают Python. Если установщик предложит добавить папку в PATH — соглашайся.
- Если пользователь уже поставил Python классическим установщиком `.exe` (он устарел с версии 3.14) — переустановить, отметив «Add python.exe to PATH», или пользоваться командой `py`.
- Если команда открывает Store: Пуск → «Управление псевдонимами выполнения приложений» (Manage app execution aliases) → проверить переключатели для Python. При Python install manager псевдонимы «Python (default)» должны быть **включены**; если Python ставился классическим установщиком — псевдонимы `python.exe` и `python3.exe` от App Installer нужно **выключить**.
- `pip` не найден → использовать `python -m pip install <пакет>` (или `py -m pip`) — так pip точно от того же Python.

**Проверка**
```powershell
python --version
python -m pip --version
```

**Профилактика:** один способ установки Python, без смешивания установщиков; пакеты ставить в venv.

**Источник:** [Using Python on Windows](https://docs.python.org/3/using/windows.html) (раздел Troubleshooting).

---

## 2. Git не найден

**Симптомы:** `git : The term 'git' is not recognized…` / «Имя "git" не распознано…».

**Исправление** — установить Git for Windows с [git-scm.com/install/windows](https://git-scm.com/install/windows) (настройки по умолчанию подходят) или через winget:
```powershell
winget install --id Git.Git -e --source winget
```
Затем закрыть и открыть PowerShell. Первая настройка (имя и почта для коммитов):
```powershell
git config --global user.name "Ваше Имя"
git config --global user.email "почта@example.com"
```

**Проверка:** `git --version` показывает версию.

**Источник:** [Install Git on Windows](https://git-scm.com/install/windows).

---

## 3. PATH: программа установлена, но не находится

PATH — список папок, в которых Windows ищет программы по имени.

**Посмотреть PATH**
```powershell
$env:Path -split ';'
```

**Добавить папку для текущего пользователя** (без прав администратора; путь заменить на свой):
```powershell
$userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
[Environment]::SetEnvironmentVariable('Path', "$userPath;C:\путь\к\папке", 'User')
```
Или вручную: Пуск → «Изменение переменных среды текущего пользователя» (Edit environment variables for your account) → Path → Изменить → Создать.

**Не использовать** `setx PATH "%PATH%;…"`: команда обрезает значение до 1024 символов и смешивает системный PATH с пользовательским — так легко испортить PATH.

**Проверка:** новое окно PowerShell → `Get-Command <программа>`.

**Источник:** [about_Environment_Variables](https://learn.microsoft.com/powershell/module/microsoft.powershell.core/about/about_environment_variables), [setx](https://learn.microsoft.com/windows-server/administration/windows-commands/setx).

---

## 4. venv: создание, активация, Activate.ps1

venv (виртуальное окружение) — отдельная папка с Python и библиотеками для одного проекта, чтобы проекты не мешали друг другу.

**Создать и включить** (в папке проекта):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
Признак успеха — `(.venv)` в начале строки. Выключить — `deactivate`.

**Частые ошибки**
- «Выполнение сценариев отключено» → раздел 5.
- `.venv\Scripts\Activate.ps1 not found` → окружение не создано или создано в другой папке; проверить `Test-Path .\.venv\Scripts\Activate.ps1`.
- В cmd (не PowerShell) включать через `.venv\Scripts\activate.bat`.
- VS Code не видит окружение → Ctrl+Shift+P → «Python: Select Interpreter» → выбрать `.venv`.

**Профилактика:** папку `.venv` добавить в `.gitignore`; список библиотек хранить в `requirements.txt`. В Windows PowerShell 5.1 сохранять его так (оператор `>` записал бы файл в кодировке UTF-16, и Git показал бы его как двоичный):
```powershell
python -m pip freeze | Out-File -Encoding utf8 requirements.txt
```

**Источник:** [venv — Creation of virtual environments](https://docs.python.org/3/library/venv.html).

---

## 5. ExecutionPolicy: «выполнение сценариев отключено»

**Симптомы**
- `File …\Activate.ps1 cannot be loaded because running scripts is disabled on this system.`
- «Невозможно загрузить файл …\Activate.ps1, так как выполнение сценариев отключено в этой системе.»

**Причина:** политика выполнения PowerShell по умолчанию запрещает запуск `.ps1`-скриптов.

**Исправление** (права администратора не нужны; `-Force` убирает вопрос подтверждения):
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
```
Без `-Force` PowerShell спросит подтверждение — ответить `Y`. `RemoteSigned`: свои скрипты запускаются, скачанные из интернета — только подписанные. Это рекомендация из документации Python.

**Не делать:** `Unrestricted` или `Bypass` для всей машины.

**Проверка**
```powershell
Get-ExecutionPolicy -List
```
У `CurrentUser` должно быть `RemoteSigned`. Если в строках `MachinePolicy` или `UserPolicy` что-то задано — политику определяет администратор (групповая политика), своей командой её не переопределить; тогда можно запускать Python окружения напрямую: `.\.venv\Scripts\python.exe файл.py`.

**Источник:** [about_Execution_Policies](https://learn.microsoft.com/powershell/module/microsoft.powershell.core/about/about_execution_policies), [venv](https://docs.python.org/3/library/venv.html).

---

## 6. Защита папки «Документы» мешает git clone

**Симптомы** (при работе в «Документах», «Рабочем столе», «Изображениях»):
- `fatal: could not create work tree dir '…': Permission denied`
- `error: unable to create file …: Permission denied`, `unable to write new index file`
- Уведомление Windows «Несанкционированные изменения заблокированы» (Unauthorized changes blocked).

**Как убедиться:** Безопасность Windows → Защита от вирусов и угроз → Журнал защиты (Protection history) — там будет запись «Доступ к защищённой папке заблокирован» с именем программы. Если на компьютере стоит сторонний антивирус (Kaspersky, ESET, Dr.Web и т. п.), встроенная защита Windows обычно отключена, и блокирует сам антивирус — разрешение нужно давать в его настройках.

**Причина:** функция «Контролируемый доступ к папкам» (Controlled folder access — защита от программ-шантажистов) не даёт неизвестным программам (git.exe, python.exe) менять файлы в защищённых папках. Ещё одна частая помеха — синхронизация «Документов» с OneDrive, которая блокирует файлы во время записи.

**Исправление (лучший вариант)** — держать проекты вне защищённых папок и OneDrive:
```powershell
New-Item -ItemType Directory -Force C:\dev
Set-Location C:\dev
git clone https://github.com/<владелец>/<репозиторий>.git
```

**Если проект нужен именно в «Документах»** — разрешить конкретную программу, не выключая защиту: Безопасность Windows (Windows Security) → Защита от вирусов и угроз (Virus & threat protection) → Управление защитой от программ-шантажистов (Manage ransomware protection) → Разрешить работу приложения через контролируемый доступ к папкам (Allow an app through Controlled folder access) → Добавление разрешённого приложения (Add an allowed app) → Недавно заблокированные приложения (Recently blocked apps) → выбрать `git.exe` (и другие заблокированные, например `python.exe`). Если программы нет в списке — «Просмотреть все приложения» (Browse all apps) и указать файл, например `C:\Program Files\Git\cmd\git.exe`. Русские названия пунктов могут немного отличаться в разных сборках Windows 10 — ориентируйтесь на английские в скобках.

**Проверка:** повторить `git clone` — ошибок и уведомлений нет.

Если команда `Get-MpPreference` (показывает настройки встроенного антивируса) выдаёт ошибку — скорее всего, стоит сторонний антивирус и встроенный отключён; пришлите текст ошибки.

**Профилактика:** все проекты — в `C:\dev` или `C:\Users\<имя>\code`.

**Источник:** [Controlled folder access (Microsoft Learn)](https://learn.microsoft.com/defender-endpoint/controlled-folders).

---

## 7. Ошибки прав на других дисках (D:, флешки, внешние диски)

**Симптомы:** «Отказано в доступе» / `Access is denied`, `Permission denied` при создании или изменении файлов на D:; часто вместе с ошибкой из раздела 10.

**Причины**
1. Папку создала программа, запущенная от администратора, — владелец «Администраторы», обычный пользователь писать не может.
2. Диск достался от старой установки Windows — владелец файлов — несуществующая старая учётная запись.
3. Флешка или внешний диск в FAT32/exFAT — там нет прав и владельцев вообще (это важно для Git, раздел 10).

**Диагностика**
```powershell
Get-Acl D:\projects | Format-List Owner, AccessToString
```

**Исправление**
- Через проводник: правый клик по папке → Свойства → Безопасность → Дополнительно → Владелец: Изменить → ввести своё имя пользователя → отметить «Заменить владельца подконтейнеров и объектов» → ОК. Потребуются права администратора.
- Или командами в PowerShell, **запущенной от администратора**. Права (кто может читать и писать) и владелец (чья это папка) — разные вещи; Git проверяет именно **владельца** (раздел 10).
  Сначала в **обычном** окне PowerShell узнайте свой логин (в окне администратора может оказаться другая учётная запись):
  ```powershell
  whoami
  ```
  Получится что-то вроде `desktop-7q2k\anna`. Затем в окне администратора — сделать себя владельцем папки и всего внутри (`/C` — не останавливаться на отдельных ошибках):
  ```powershell
  icacls "D:\projects" /setowner "desktop-7q2k\anna" /T /C
  ```
  И при необходимости дать себе полный доступ:
  ```powershell
  icacls "D:\projects" /grant "desktop-7q2k\anna:(OI)(CI)F" /T /C
  ```
  Команду `takeown /D Y` лучше не использовать: ответ на её вопрос зависит от языка Windows, и на русской системе `Y` может не сработать.

**Профилактика:** не запускать редактор и терминал от администратора без нужды; проекты держать на NTFS-диске.

**Источник:** [icacls](https://learn.microsoft.com/windows-server/administration/windows-commands/icacls).

---

## 8. venv сломался после переноса или переименования папки

**Симптомы:** после перемещения проекта
- `Fatal error in launcher: Unable to create process using '"C:\старый\путь\.venv\Scripts\python.exe" …'`
- `(.venv)` в строке есть, но `pip` и `python` берутся не оттуда или не запускаются.

**Причина:** venv хранит **абсолютные пути** к своей старой папке (в скриптах активации и в `pip.exe`). venv нельзя переносить — его пересоздают.

**Исправление** (в папке проекта; удаляется только папка окружения, код не трогается).

Сначала сохраните список библиотек (python.exe окружения после переноса обычно ещё работает, ломаются pip.exe и скрипты активации):
```powershell
.\.venv\Scripts\python.exe -m pip freeze | Out-File -Encoding utf8 requirements-old.txt
```
Затем (`deactivate` — только если окружение сейчас включено):
```powershell
deactivate
Remove-Item -Recurse -Force .\.venv
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```
Если `requirements.txt` нет — используйте сохранённый `requirements-old.txt`. Если и сохранить не удалось — посмотрите `import` в коде и поставьте библиотеки заново.

**Проверка:** `python -c "import sys; print(sys.prefix)"` показывает новый путь; программа запускается.

**Профилактика:** `.venv` в `.gitignore`, `requirements.txt` в репозитории; после переноса проекта — всегда пересоздавать окружение.

**Источник:** [venv](https://docs.python.org/3/library/venv.html) («not considered as movable or copyable»).

---

## 9. При копировании проекта потерялась скрытая папка .git

**Симптомы:** в скопированной папке `fatal: not a git repository (or any of the parent directories): .git`; история и связь с GitHub пропали.

**Причины:** папка `.git` скрытая. Проводник её не показывает, и при выделении «всех видимых файлов» она не копируется. Ещё причины: проект скачан с GitHub как ZIP (там `.git` нет), архиватор или облачная синхронизация пропустили скрытые файлы.

**Диагностика**
```powershell
Get-ChildItem -Force
Test-Path .git
```

**Исправление**
- Если старая папка цела — скопировать **всю папку целиком**, включая скрытое:
  ```powershell
  robocopy "C:\старое\место\проект" "D:\новое\место\проект" /E
  ```
  `robocopy` возвращает коды 0–7 при успехе (1 — «файлы скопированы»), это не ошибка.
- Если старой `.git` нет, но проект есть на GitHub — склонировать заново в новую папку, затем перенести туда свои изменённые файлы (без папки `.git`), проверить `git status`.

**Проверка:** `git status` и `git log --oneline -3` работают; `git status` пишет «On branch main» / «На ветке main».

**Профилактика:** включить показ скрытых элементов (Проводник → Вид → «Скрытые элементы»); переносить проект через `git clone`, а не копированием.

**Источник:** [robocopy](https://learn.microsoft.com/windows-server/administration/windows-commands/robocopy).

---

## 10. Git: «detected dubious ownership»

**Симптомы**
```
fatal: detected dubious ownership in repository at 'D:/projects/repo'
'D:/projects/repo' is owned by: …
but the current user is: …
To add an exception for this directory, call:
	git config --global --add safe.directory D:/projects/repo
```

**Причина:** Git отказывается работать в папке, владелец которой — другой пользователь (защита от уязвимости CVE-2022-24765). Бывает на других дисках, на флешках с FAT32/exFAT (там владельца нет), в папках, созданных от администратора, в репозиториях, скопированных с другого компьютера.

**Исправление**
- Лучше — сделать себя владельцем папки (раздел 7, команда `icacls … /setowner`). Это не сработает на флешках FAT32/exFAT — там владельцев нет, остаётся только вариант ниже.
- Если папка ваша и вы ей доверяете — выполнить ту команду, которую подсказал сам Git, **с путём из сообщения** (прямые слэши `/`, как у Git):
  ```powershell
  git config --global --add safe.directory 'D:/projects/repo'
  ```
- **Не использовать** `safe.directory '*'` — это отключает защиту для всех папок.

**Проверка:** `git status` работает без ошибки и начинается с «On branch …» / «На ветке …».

**Источник:** [git-config: safe.directory](https://git-scm.com/docs/git-config#Documentation/git-config.txt-safedirectory).

---

## 11. Конфликты при git pull

**а) Локальные изменения мешают**
```
error: Your local changes to the following files would be overwritten by merge:
Please commit your changes or stash them before you merge.
```
Исправление — сохранить свои изменения, потом забрать чужие (`--no-edit` — чтобы Git не открывал текстовый редактор для сообщения о слиянии):
```powershell
git add -A
git commit -m "Мои изменения"
git pull --no-edit
```
Или временно отложить: `git stash`, затем `git pull`, затем `git stash pop`.

**б) Конфликт содержимого**
```
CONFLICT (content): Merge conflict in app.py
Automatic merge failed; fix conflicts and then commit the result.
```
Что значит: вы и кто-то другой (или вы на другом компьютере) изменили одни и те же строки. В файле появились метки:
```
<<<<<<< HEAD
ваш вариант
=======
пришедший вариант
>>>>>>> …
```
Исправление: открыть файл (в VS Code есть кнопки «Accept Current / Incoming / Both»), оставить нужный текст, **удалить все метки**, затем:
```powershell
git add app.py
git commit --no-edit
```
Если всё же открылся непонятный редактор с текстом «Merge branch…» (это Vim) — наберите `:wq` и нажмите Enter.
Передумали — вернуть всё как было до pull: `git merge --abort`.

**в) Git просит выбрать способ**
```
fatal: Need to specify how to reconcile divergent branches.
```
Для новичка проще всего слияние (merge):
```powershell
git config --global pull.rebase false
git pull --no-edit
```

**г) Push отклонён**
```
! [rejected] main -> main (fetch first)
Updates were rejected because the remote contains work that you do not have locally.
```
Сначала `git pull` (при конфликте — пункт «б»), потом `git push`. **Не использовать** `git push --force` — это сотрёт чужие изменения на сервере.

**Проверка:** `git status` пишет «nothing to commit, working tree clean» / «нечего коммитить, нет изменений в рабочем каталоге», `git log --oneline -5` показывает коммит слияния.

**Профилактика:** перед началом работы — `git pull`; коммитить часто и небольшими порциями.

**Источник:** [git-pull](https://git-scm.com/docs/git-pull), [Basic merge conflicts (Pro Git)](https://git-scm.com/book/en/v2/Git-Branching-Basic-Branching-and-Merging).

---

## 12. ModuleNotFoundError: библиотека установлена, но не находится

**Симптомы:** `ModuleNotFoundError: No module named 'requests'` (или другая библиотека), хотя «вчера ставил».

**Причины** (по вероятности)
1. Библиотека стоит в виртуальном окружении, а оно сейчас не включено (новое окно PowerShell — окружение нужно включать заново).
2. На компьютере несколько Python: `pip` ставит в один, `python` запускает другой.
3. Редактор (VS Code, PyCharm) запускает другой интерпретатор (программу, которая выполняет код), чем терминал.

**Диагностика** (в папке проекта)
```powershell
python -c "import sys; print(sys.executable)"
```
```powershell
where.exe python
```
```powershell
python -m pip show requests
```
Первая — какой Python запускается сейчас; вторая — сколько их найдено (несколько строк = несколько Python); третья — стоит ли библиотека именно в этот Python (`WARNING: Package(s) not found` — нет).

**Исправление**
- Есть папка `.venv` — включить окружение: `.\.venv\Scripts\Activate.ps1` (ошибка «выполнение сценариев отключено» — раздел 5).
- Поставить библиотеку в тот Python, который запускает программу:
  ```powershell
  python -m pip install requests
  ```
- VS Code: Ctrl+Shift+P → «Python: Select Interpreter» → выбрать Python из `.venv`.

**Проверка:** `python -c "import requests; print(requests.__version__)"` печатает номер версии.

**Профилактика:** один проект — одно окружение `.venv`; ставить библиотеки только командой `python -m pip install …` при включённом окружении; список — в `requirements.txt` (раздел 4).

**Источник:** [Installing packages using pip and virtual environments](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/), [venv](https://docs.python.org/3/library/venv.html).
