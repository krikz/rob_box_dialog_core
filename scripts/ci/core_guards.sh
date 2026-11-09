#!/usr/bin/env bash
# Гарды кода ядра (копия гардов rob_box_project, ADR-0167 §2.1, §6). Запуск из корня репо: bash scripts/ci/core_guards.sh
#
# cc_budget / class_budget - по каталогам ядра явно: так фантомы baseline считаются только среди просканированных файлов,
# записи baseline про файлы робота ядро не трогают. temp_adr0148_check - по src/ (это и есть ядро).
# seam_without_consumer ищет потребителя шва по всему дереву - в CI его гоняют после наложения чекаута робота
# (шаг «Robot checkout for cross-checks»), иначе потребители робота не видны и каждый топик ядра - «шов без потребителя».
set -euo pipefail
PY="${PYTHON:-python}"
CORE=(
  src/rob_box_core/rob_box_core
  src/rob_box_llm/rob_box_llm
  src/rob_box_harness/rob_box_harness
  src/rob_box_dialog/rob_box_dialog
  src/rob_box_dialog_host/rob_box_dialog_host
  src/rob_box_music/rob_box_music
  src/rob_box_mcp_tools/rob_box_mcp_tools
)
"$PY" scripts/lint/cc_budget.py "${CORE[@]}"
"$PY" scripts/lint/class_budget.py "${CORE[@]}"
"$PY" scripts/lint/temp_adr0148_check.py
if [ "${WITH_SEAM:-0}" = "1" ]; then
  "$PY" scripts/lint/seam_without_consumer.py
fi
