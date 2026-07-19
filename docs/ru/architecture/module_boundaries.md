# Границы модулей

Документ перечисляет официальные границы проекта. Новый код должен импортировать конкретный модуль, который соответствует его задаче.

## Запуск приложения

### `src/app/entrypoint.py`

Каноническая и единственная точка запуска, перезапуска и синхронизации runtime session.

Корневой `tool.py` импортирует запуск напрямую отсюда. UI слой не содержит entrypoint и не зависит от application слоя.

## Главное окно

### `src/app/composition/main_window.py`

`create_main_window()` создаёт главное окно и передаёт ему каталог текстов и путь Tk DnD.

`compose_main_window()` собирает вкладки, настройки, project workspace, Plugin Manager и правую панель.

UI класс `src/ui/main_window.py` не вызывает composition самостоятельно.

## Composition

### `src/app/composition`

Это единственное место, где application слой создаёт concrete UI классы и связывает их с controller, service, runtime и локализацией.

## Окна и диалоги

### `src/ui/common/windowing.py`

Содержит общий класс `Toplevel`, определение владельца окна, подготовку первого кадра и централизованное поднятие нового окна на передний план. Новые окна интерфейса не должны импортировать `tkinter.Toplevel` напрямую.

### `src/ui/common/window_appearance.py`

Хранит текущую тему и прозрачность зарегистрированных корневых и дочерних окон. Изменения оформления применяются ко всем живым окнам через этот реестр.

### `src/ui/common/window_paint.py`

Выполняет ограниченную отрисовку первого кадра: обрабатывает layout и нативные оконные события, но не запускает посторонние Tk timer и file callbacks.

### `src/ui/common/window_reveal.py`

Показывает подготовленное корневое окно только после отрисовки первой нативной поверхности. В Windows использует alpha gate и временное размещение за пределами экрана, чтобы не допустить появления белого кадра без темы.

### `src/ui/startup_splash.py`

Показывает управляемый приложением startup splash после включения файлового журнала, а финальное появление главного окна передаёт общему reveal pipeline.

### `src/app/composition/dialogs.py`

Связывает application слой с предупреждениями, подтверждениями и файловыми диалогами. В Windows файловым диалогам передаётся активное окно владельца.

## Локализация

### `src/app/localization_selection.py`

Загружает выбранный языковой каталог на основе сохранённой настройки.

### `src/app/localization_runtime.py`

Хранит application каталог локализации.

### `src/ui/localization.py`

Содержит только Protocol `LocalizationCatalog`.

UI получает каталог явно и не импортирует application singleton.

## Настройки

### `src/platform/settings_repository.py`

Читает и сохраняет корневой `config/settings.ini`. Не запускает application поведение и не выбирает язык.

### `src/app/settings`

Координирует изменение настроек и связанные application действия.

## Platform

### `src/platform`

Содержит технические адаптеры файловой системы, JSON, INI, языков, сети, процессов, Git, logging и desktop shell.

Platform не выбирает пользовательский сценарий и не содержит правил обработки образов.

Конфигурация и инфраструктурные адаптеры используют перечисленные здесь конкретные границы; дополнительного верхнего слоя исходников нет.

## Корневые данные

### `config`

Содержит редактируемые настройки приложения.

### `languages`

Содержит динамически обнаруживаемые языковые JSON файлы.

### `plugins`

Содержит единственную локальную базу `plugin_db.json` и каталог `installed`.

### `temp`

Содержит только временные загрузки и рабочие файлы.

### `templates/ota`

Содержит OTA шаблоны незавершённого сценария payload packing. Они не являются активными настройками.

## Runtime

### `src/app/runtime/session.py`

Создаёт одну runtime session и регистрирует core services.

### `src/app/runtime/phases.py`

Регистрирует и читает четыре типизированные runtime фазы.

### `src/app/runtime/models.py`

Содержит dataclass модели runtime фаз.

### `src/app/runtime/contexts`

Содержит узкие resolver модули только для application слоя.

Корневой `__init__.py` ничего не переэкспортирует.

## Фоновые задачи и UI поток

### `src/app/background_jobs.py`

Создаёт application managed background job.

### `src/app/ui_tasks.py`

Запускает рабочую функцию и доставляет завершение через UI dispatcher.

### `src/app/ui_feedback.py`

Содержит application координацию уведомлений и доставку результата через предоставленный UI dispatcher.

### `src/logic/common/service_output.py`

Содержит нейтральный канал сообщений и прогресса для logic.

## Диагностика и ошибки core

### `src/core/diagnostics.py`

Предоставляет независимый sink для диагностических событий core. По умолчанию используется стандартный `logging`, а конкретная операция может явно подменить sink.

### `src/core/errors.py`

Содержит общие типизированные ошибки низкоуровневого слоя.

## MTK Port Tool

### `src/core/mtk_port`

Работа с boot image, безопасной ZIP распаковкой, property файлами и updater script.

### `src/logic/tools/mtk_port_tool`

Модели, профили и последовательность портирования.

### `src/app/composition/mtk_port_tool.py`

Composition функции.

### `src/ui/tabs/tools/mtk_port_tool`

Окно и presentation поведение.

Код MTK Port Tool остаётся внутри этих четырёх явных границ пакетов.

## Проекты

### `src/logic/projects`

Domain модели, проверки и рабочие операции проектов.

### `src/app/projects`

Application controller проектных сценариев.

### `src/ui/tabs/project`

View, presenter и presentation controller проектов.

## Плагины

### `src/logic/plugins`

Domain модели и plugin operations.

### `src/app/plugins`

Application workflow, repositories и runtime adapters.

### `src/ui/tabs/plugins`

Окна, формы, карточки и presentation state.

## Обновление

### `src/logic/update`

Release модели и операции подготовки файлов.

### `src/app/update_controller.py`

Application state machine обновления.

### `src/app/update_orchestrator.py`

Последовательность применения и очистки обновления.

### `src/ui/update`

Окно и presentation controller.

## Низкоуровневые операции

### `src/core`

Образы, архивы, процессы, форматы данных и файловые примитивы.

Core не является composition границей и не предоставляет UI facade.

## Типизированные Plugin и Tk границы

### `src/logic/plugins/store_models.py`

Проверяет внешний JSON каталога и создаёт неизменяемые `PluginCatalogItem`.

### `src/logic/plugins/runtime/registry.py`

Хранит `VirtualPluginInfo` и типизированные plugin callable. Результат стороннего плагина остаётся непрозрачным `object` до явной проверки потребителем.

### `src/logic/plugins/config/service.py`

Преобразует конфигурацию окна плагина в `PluginDialogConfig`, `PluginConfigInfo`, `PluginControlGroup` и `PluginControlConfig`.

### `src/app/runtime/contexts/contracts.py`

Содержит точные runtime Protocol для scheduler, task runner, состояния и Plugin Store. Общий контракт не использует `Any`.

### `src/app/ui_feedback.py`

Передаёт уведомление через явные поля `text`, `color`, `title` и `master`. Каталог локализации связывается с реальным диалогом в главном окне.

### `scripts/quality/check_typed_boundaries.py`

Запускает строгую Mypy проверку выбранных архитектурных границ.

Подробное описание находится в `typed_boundaries.md`.
