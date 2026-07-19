# Runtime окружение

## Python зависимости

Установка зависимостей программы выполняется из корня репозитория.

```bash
python -m pip install -r requirements.txt
```

Инструменты ручной проверки устанавливаются отдельно.

```bash
python -m pip install -r requirements-quality.txt
```

`requirements-quality.txt` не используется GitHub Actions и не нужен пользователю готовой программы.

Запуск из исходников поддерживает Python 3.10 и новее. Текущий GitHub Actions workflow собирает приложение на Python 3.12.

## Системные зависимости

Windows использует встроенный Tk из официального Python.

Linux требует Tk и LZO. GitHub Actions устанавливает `python3-tk` и `liblzo2-dev` только для сборки Linux версии.

macOS использует окружение выбранного runner и зависимости из `requirements.txt`.

## Ручные проверки окружения

```bash
python scripts/quality/check_system_dependencies.py
python scripts/quality/check_required_dependencies.py --smoke-only
python scripts/quality/check_required_assets.py
```

Эти команды не запускаются автоматически при сборке.

## GUI проверки в Linux

При наличии Xvfb графические проверки можно запустить так:

```bash
xvfb-run -a python scripts/manual/manual_gui_smoke.py --full
```

GitHub Actions не запускает этот набор. Он предназначен только для ручной проверки.

## Runtime каталоги

Готовая программа хранит редактируемые данные рядом с исполняемым файлом.

```text
<корень программы>/
  bin/
  config/
    settings.ini
    context_rules.json
    mtk_port_profiles.json
  languages/
  plugins/
    plugin_db.json
    installed/
  temp/
    plugins/
      downloads/
      runtime/
    updates/
    magisk/
    mtk_port/
  templates/
    ota/
  logs/
```

Пользовательские проекты создаются в рабочем каталоге, выбранном в настройках. Каждый проект содержит `input`, `unpack` и `output`.

## Назначение каталогов

### `bin`

Содержит внешние исполняемые инструменты и связанные с ними ресурсы. Настройки программы и установленные плагины здесь не хранятся.

### `config`

Содержит редактируемую конфигурацию приложения. Файлы лучше изменять только при закрытой программе.

### `languages`

Программа динамически сканирует `languages/*.json`. Для добавления языка не требуется менять исходный код, если JSON содержит обязательные ключи и корректные метаданные.

### `plugins`

`plugins/plugin_db.json` является единственной локальной базой Plugin Store.

Установленные плагины находятся в `plugins/installed`.

Архивы загрузки и временная распаковка находятся в `temp/plugins`.

### `temp`

Содержит только временные данные программы. Установленные модули находятся в `plugins/installed`; runtime-resolver не ищет альтернативные корни.

### `templates/ota`

Содержит шаблоны незавершённой поддержки упаковки payload. Текущие активные окна Tools не используют эти файлы.

### Ресурсы интерфейса

Изображения и загрузчик ресурсов находятся в `src/ui/assets` в исходном проекте. Отдельного корневого каталога `assets` нет.

## GitHub Actions

Workflow `.github/workflows/build.yml` выполняет только следующие действия:

1. Получает исходный код.
2. Устанавливает Python 3.12.
3. Устанавливает `requirements.txt`.
4. Запускает `build.py` для выбранной платформы.
5. Проверяет готовые ZIP архивы перед публикацией.
6. Публикует релиз, если это разрешено параметрами запуска.

Workflow не вызывает файлы из `scripts`, Pytest, Ruff, Mypy и Architecture Guard.

## Очистка release архива

`scripts/release/build_release_archive.py` исключает сгенерированное содержимое из:

```text
plugins/installed
temp
logs
Projects
```

Также в пользовательскую сборку не входят `docs`, `tests`, `scripts`, `src`, `.github` и конфигурация инструментов разработки.

## Перезапуск приложения

При смене языка frozen приложение запускает новый процесс через `src/platform/process_restart.py`.

Для PyInstaller onefile новый процесс получает `PYINSTALLER_RESET_ENVIRONMENT=1`. Это заставляет его создать собственный временный каталог и не зависеть от файлов старого экземпляра.
