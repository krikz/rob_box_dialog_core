#!/usr/bin/env bash
# Наложить файлы робота (чекаут krikz/rob_box_project) на рабочую копию ядра для сверок «ядро ↔ робот» в CI.
#
# Зачем: часть тестов ядра сверяет ядро с файлами робота (профиль робота, rob_box_dialog_msgs, сценарии марафона,
# вердикт шага e2e_tool_match, хосты робота). До ADR-0167 Ш3/Ш5 они живут в репо ядра и идут на чекауте робота.
#
# Правило: НИ ОДИН файл ядра не перезаписывается. Каталоги ядра исключены целиком (иначе старые копии ядра из
# rob_box_project, пока они там есть, воскресили бы удалённые здесь файлы), остальное - --ignore-existing.
#
#   bash scripts/ci/robot_overlay.sh <каталог чекаута робота>
set -euo pipefail
ROBOT="${1:?каталог чекаута rob_box_project}"
[ -d "$ROBOT/src" ] || { echo "нет $ROBOT/src - это не чекаут rob_box_project" >&2; exit 2; }
REV="$(git -C "$ROBOT" rev-parse HEAD 2>/dev/null || echo '?')"
rsync -a --ignore-existing \
  --exclude=/.git \
  --exclude=/.github/workflows \
  --exclude=/src/rob_box_core \
  --exclude=/src/rob_box_llm \
  --exclude=/src/rob_box_harness \
  --exclude=/src/rob_box_dialog \
  --exclude=/src/rob_box_dialog_host \
  --exclude=/src/rob_box_music \
  --exclude=/scripts/dialog \
  --exclude=/scripts/dialogue \
  --exclude=/scripts/lint \
  --exclude=/scripts/ci/core_guards.sh \
  --exclude=/scripts/ci/robot_overlay.sh \
  --exclude=/tests/unit/dialog \
  --exclude=/packaging \
  --exclude=/pyproject.toml \
  --exclude=/pytest.ini \
  --exclude=/conftest.py \
  --exclude=/README.md \
  --exclude=/AGENTS.md \
  "$ROBOT/" ./
rm -rf -- "./${ROBOT#./}"
echo "наложены файлы робота rob_box_project@$REV"
