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

## Что внутри

| Каталог | Что |
|---|---|
| `src/rob_box_core` | общие типы, миграции памяти (`migrations/*.sql`), зеркало сообщений диалога |
| `src/rob_box_llm` | провайдеры LLM, STT и TTS |
| `src/rob_box_harness` | агентный каркас: агенты, решения, политика подтверждений |
| `src/rob_box_dialog` | ход диалога, адресация, профиль продукта, фразы и основы промптов |
| `src/rob_box_dialog_host` | связка хода: мост команд, порты диалога, память, каталог голосов |
| `src/rob_box_music` | модель музыки (её знание читают фразы медиа) |
| `src/rob_box_mcp_tools` | только `owner_event`, `voice_request`, `base` (полный пакет живёт у робота) |
| `scripts/dialog`, `scripts/dialogue` | сухой стенд, сухой марафон, консоль `chat.py` |
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

Правка ядра делается PR в этот репозиторий. После CI и мёржа ставится тег `vX.Y.Z`. Если меняется порт или формат профиля,
поднимается мажорная версия. Потребитель поднимает тег отдельным PR у себя (ADR-0167 §3).
