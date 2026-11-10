# rob_box_dialog_core

Ядро диалога РОББОКСа без ROS: ход, адресация, мост команд LLM, память, фразы, адаптеры речи и консоль.
Пакет `rob-box-dialog-core`. Его ставят робот (`krikz/rob_box_project`) и колонка (`krikz/rob_box_station`).
Решение и границы описаны в ADR-0167 в `rob_box_project` (`docs/adr/0167-dialog-core-repo-and-station-repo.md`).

Репозиторий вынесен из `rob_box_project` вместе с историей (`git filter-repo` по путям ядра, ADR-0167 шаг Ш2).
Пути внутри остались прежними (`src/<пакет>/<пакет>`), поэтому `git log -- <файл>` показывает и историю до переезда.

## Установка

```bash
# по тегу (репозиторий публичный)
pip install "rob-box-dialog-core @ git+https://github.com/krikz/rob_box_dialog_core@v0.1.0"

# из чекаута, с тестовыми зависимостями
pip install ".[test]"
```

Нужен Python 3.10 или новее. Зависимости: PyYAML, openai, httpx. ROS не нужен.

Консоль стенда (сухой ход v2, без ROS и железа) — entry point `rbx-chat`:

```bash
rbx-chat --once "Сколько у тебя заряда?" --once "Робот, стоп"   # сценарий, затем выход
rbx-chat --providers deepseek --debug                            # интерактивно
```

Заменяет `python scripts/dialogue/chat.py`. Скрипты стенда лежат в пакете как package-data
(`rob_box_dialog_console.data.scripts`); ключи — из `scripts/dialogue/.env` или окружения.

## Что внутри

| Каталог | Что |
|---|---|
| `src/rob_box_core` | общие типы, миграции памяти (`migrations/*.sql`), зеркало сообщений диалога |
| `src/rob_box_llm` | провайдеры LLM, STT и TTS (`stt_providers/minimax_provider` — распознавание MiniMax) |
| `src/rob_box_harness` | агентный каркас: агенты, решения, политика подтверждений |
| `src/rob_box_dialog` | ход диалога, адресация, профиль продукта, фразы и основы промптов |
| `src/rob_box_dialog_host` | связка хода: мост команд, порты диалога, память, каталог голосов |
| `src/rob_box_music` | модель музыки (её знание читают фразы медиа) |
| `src/rob_box_mcp_tools` | ROS-free часть: `base`, `owner_event`, `voice_request` + тул `tools.web_search` (поиск) |
| `scripts/dialog`, `scripts/dialogue` | сухой стенд, сухой марафон, консоль `chat.py` (entry point `rbx-chat`) |
| `scripts/lint` | копия гардов кода робота (CC, классы, швы, `TEMP(ADR-0148)`) |

Сборку описывает один `pyproject.toml` в корне. Файлы `package.xml` и `setup.py` в `src/<пакет>/` нужны colcon робота.
Робот собирает ими ядро, пока не перейдёт на установку по тегу (ADR-0167 Ш3).

## Проверка

```bash
pip install ".[test]"
ROB_BOX_CORE_FROM_PACKAGE=1 bash -c 'cd src/rob_box_dialog && pytest test'   # и так для каждого пакета
bash scripts/ci/core_guards.sh                                              # гарды ядра
```

CI (`.github/workflows/ci.yml`) проверяет на Python 3.10, 3.11 и 3.12. Часть тестов сверяет ядро с файлами робота:
профилем робота, `rob_box_dialog_msgs`, сценариями марафона, хостами. Для них CI накладывает чекаут публичного
`rob_box_project@develop` (`scripts/ci/robot_overlay.sh`). Файлы ядра при этом не перезаписываются.

## Версии

Правка ядра делается PR в этот репозиторий. После CI и мёржа ставится тег `vX.Y.Z`. Ш3 (v0.7.2) добавил в пакет
адаптеры речи (`rob_box_llm.stt_providers.minimax_provider`), тул поиска `rob_box_mcp_tools.tools.web_search`
и консоль `rbx-chat` (добавка модулей, существующий порт не сломан — patch). Если меняется порт или формат профиля,
поднимается мажорная версия. Потребитель поднимает тег отдельным PR у себя (ADR-0167 §3).
