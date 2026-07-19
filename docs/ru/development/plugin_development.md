# Разработка плагинов

Этот документ описывает текущий формат плагинов по реальному коду application, logic и platform слоёв.

## Где находятся плагины

Установленные плагины хранятся в:

```text
plugins/installed/<identifier>/
```

Каталог плагина считается установленным, если в нём есть файл `info.json`.

## Минимальная структура Python плагина

```text
plugins/installed/example_plugin/
  info.json
  main.py
```

Пример `info.json`:

```json
{
  "identifier": "example_plugin",
  "name": "Example Plugin",
  "version": "1.0",
  "author": "Author",
  "describe": "Описание плагина",
  "depend": ""
}
```

Поле `identifier` должно совпадать с именем каталога.

Файл `main.py` должен содержать функцию `main` или словарь `entrances`.

Простой вариант:

```python
def main(**values):
    print(values)
```

При запуске MIO Kitchen сопоставляет имена параметров функции со значениями runtime. Обязательный параметр без соответствующего значения вызывает ошибку регистрации или вызова.

Вариант с несколькими точками входа:

```python
from src.logic.plugins.runtime import Entry


def run_main(**values):
    print(values)


def before_pack(**values):
    print(values)


entrances = {
    Entry.main: run_main,
    Entry.before_pack: before_pack,
}
```

Доступные значения `Entry` определены в `src/logic/plugins/runtime/registry.py`.

Точка входа `Entry.before_pack` вызывается только при фактическом запуске сборки разделов. Открытие окна параметров, просмотр настроек и закрытие через «Отмена» не считаются запуском сборки и не вызывают плагин.

## Как запускается плагин

Пользовательский интерфейс собирает идентификатор плагина и значения формы. `PluginManagerController` в application слое организует сценарий и обращается к порту `PluginGatewayProtocol`. Application не читает файлы плагина и не исполняет сторонний код.

`PluginGateway` в platform слое проверяет каталог, `info.json`, зависимости и наличие точек входа. `plan_plugin_execution` в logic слое принимает результат проверки и формирует чистый план без доступа к файлам и процессам. После этого application передаёт готовый план обратно platform адаптеру.

Фактическая загрузка `main.py` и запуск внешнего `main.sh` находятся в platform слое. Такая цепочка сохраняет разделение ответственности:

```text
UI
  → PluginManagerController, application
  → PluginGatewayProtocol
  → PluginGateway inspection, platform
  → plan_plugin_execution, logic
  → PluginGateway execution, platform
```

## Shell плагин

Shell плагин использует `main.sh` вместо `main.py`.

```text
plugins/installed/example_shell_plugin/
  info.json
  main.sh
```

MIO Kitchen запускает `main.sh` через BusyBox. Перед запуском создаются переменные окружения из runtime значений и следующие служебные переменные:

| Переменная | Значение |
|---|---|
| `tool_bin` | Каталог внешних инструментов |
| `version` | Версия MIO Kitchen |
| `language` | Текущий язык |
| `bin` | Каталог текущего плагина |
| `moddir` | Общий каталог установленных плагинов |
| `project_output` | Каталог `output` текущего проекта |
| `project` | Рабочий каталог текущего проекта |

Shell плагин требует выбранный проект.

## Зависимости плагина

Поле `depend` содержит идентификаторы других плагинов через пробел.

```json
{
  "depend": "base_plugin helper_plugin"
}
```

Перед запуском и установкой MIO Kitchen проверяет наличие этих каталогов в `plugins/installed`.

## Конфигурация окна плагина

Если в каталоге есть `main.json`, Plugin Manager может использовать его как описание элементов конфигурации плагина.

Путь определяется методом `plugin_config_path` в `src/logic/plugins/module_manager.py`.

Формат проверяется моделями из `src/logic/plugins/config/service.py`. Перед добавлением новых полей нужно сверять их с этим кодом, а не только с примерами старых плагинов.

## Формат MPK

MPK является ZIP архивом со следующей структурой:

```text
plugin.mpk
  info
  main.zip
  icon
```

`icon` необязателен.

`info` является INI файлом с секцией `[module]`.

Пример:

```ini
[module]
identifier = example_plugin
name = Example Plugin
version = 1.0
author = Author
describe = Описание плагина
resource = main.zip
system = all
arch = all
depend =
```

`main.zip` содержит файлы, которые будут распакованы в каталог установленного плагина.

Установщик проверяет:

1. Архив является корректным ZIP.
2. В архиве есть `info`.
3. В `info` есть `identifier` и `resource`.
4. Указанный resource файл существует.
5. Платформа соответствует `supports` или `system`.
6. Архитектура соответствует `arch`.
7. Установлены зависимости из `depend`.

## Экспорт MPK

Plugin Manager создаёт MPK из установленного каталога.

При экспорте:

1. `info.json` преобразуется в INI файл `info`.
2. Все остальные файлы, кроме `icon`, упаковываются в `main.zip` или resource с другим именем.
3. `icon` добавляется отдельно, если существует.

Рабочая логика находится в `src/logic/plugins/export/service.py`.

## Создание заготовки

Встроенная функция создания плагина создаёт каталог и файл `info.json`. Она не создаёт рабочий `main.py` автоматически.

После создания заготовки нужно вручную добавить точку входа `main.py` или внешний `main.sh`. Эти файлы находятся только в каталоге установленного плагина. Они не являются служебными скриптами проекта в `src`.

## Безопасность

Python плагин выполняется внутри процесса MIO Kitchen и может выполнять произвольный код с правами текущего пользователя.

Shell плагин запускается через внешнюю оболочку и также имеет доступ к файлам текущего пользователя.

Устанавливать следует только доверенные плагины. Текущая реализация не использует изолированную песочницу.

## Проверки после изменения системы плагинов

```bash
python scripts/quality/check_typed_boundaries.py
python scripts/arch_guard/main.py
python -m pytest tests/unit/logic tests/integration tests/functional -q --rootdir=. -c scripts/config/pytest.ini
```

Полный ручной набор:

```bash
python scripts/manual/manual_unit_contracts.py
```
