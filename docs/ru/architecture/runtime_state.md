# Runtime State Contract

## Источник истины

Runtime находится только в `src/app/runtime`.

Вне этого пакета application-код не определяет параллельные runtime-фасады.

## Runtime session

`src/app/runtime/session.py` создаёт одну `RuntimeSession`.

Session выполняет следующие действия.

1. Регистрирует ранние значения.
2. Подготавливает platform окружение.
3. Создаёт обязательные core services.
4. Регистрирует core runtime phase.
5. Проверяет обязательные ключи фазы.

## Типизированные фазы

`src/app/runtime/phases.py` хранит четыре независимые dataclass модели.

1. `EarlyRuntimeDefaults`.
2. `RuntimeBootstrapServices`.
3. `BootstrapWindowRuntime`.
4. `BootstrapUiRuntime`.

Вторичного generic key value store нет.

Отсутствующая обязательная фаза вызывает `MissingRuntimeValueError`.

## Регистрация

Официальные функции регистрации выглядят так.

1. `register_early_runtime_defaults`.
2. `register_core_runtime_services`.
3. `register_bootstrap_window_runtime`.
4. `register_bootstrap_ui_runtime`.

Частичное обновление выполняют функции `sync_registered_*`.

## Чтение

Application код использует `require_registered_*`, если значение обязательно.

Application код использует `get_registered_*`, только если отсутствие фазы является допустимым состоянием жизненного цикла.

Новый код не читает runtime через строковый ключ.

## Context модули

`src/app/runtime/contexts` содержит узкие application resolver модули.

1. `paths.py`.
2. `tooling.py`.
3. `projects.py`.
4. `project_ui.py`.
5. `plugins.py`.
6. `settings.py`.
7. `ui.py`.
8. `project_defaults.py`.
9. `contracts.py`.

Корневой `src/app/runtime/contexts/__init__.py` не переэкспортирует значения.

Каждый resolver импортируется из своего конкретного модуля; общего широкого resolver нет.

## Правила доступа

1. Core не импортирует runtime.
2. Logic не импортирует runtime.
3. UI не импортирует runtime.
4. Runtime resolver функции используются только внутри app.
5. Composition root передаёт готовые зависимости в UI и controller.
6. Logic получает только данные, модели и явные порты операции.
7. Обязательная зависимость не заменяется значением по умолчанию.
8. Имена runtime-полей точные; поиск по alias не поддерживается.

## Window runtime

`BootstrapWindowRuntime` содержит следующие значения.

1. `main_window`.
2. `animation`.
3. `ui_scheduler`.
4. `current_project_name`.
5. `theme`.
6. `language`.

Каноническое имя главного окна только `main_window`.

Runtime-accessor требует точное имя поля `main_window`.

## UI runtime

`BootstrapUiRuntime` содержит основные UI поверхности, которые существуют после composition главного окна.

1. `unpack_view`.
2. `project_menu`.

## Автоматическая защита

Architecture Guard проверяет следующие условия.

1. Runtime находится в `src/app/runtime`.
2. Runtime-фасады не определяются вне runtime-пакета.
3. Core, logic и UI не импортируют runtime.
4. Между runtime модулями и остальным проектом нет статических циклов.
