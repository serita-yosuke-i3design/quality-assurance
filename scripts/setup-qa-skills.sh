#!/usr/bin/env bash
# プロジェクトへ QA Skills を初回配置する
#
# 用法:
#   ./scripts/setup-qa-skills.sh ../your-project
#   ./scripts/setup-qa-skills.sh ../your-project --include-beta
#
# 既定: skill-catalog の tier=distributed のみ
# セットアップ後: .cursor/qa-profile.yaml の paths を編集

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
QA_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

usage() {
  echo "Usage: $0 <project-path> [--include-beta]" >&2
  exit 1
}

[[ $# -lt 1 ]] && usage

PROJECT_ARG="$1"
shift || true

INCLUDE_BETA=false
while [[ $# -gt 0 ]]; do
  case "$1" in
    --include-beta)
      INCLUDE_BETA=true
      shift
      ;;
    *)
      usage
      ;;
  esac
done

PROJECT_PATH="$(cd "${PROJECT_ARG}" && pwd)"

echo "project: ${PROJECT_PATH}"
if [[ "${INCLUDE_BETA}" == true ]]; then
  echo "tiers: distributed, beta"
else
  echo "tiers: distributed"
fi

mkdir -p "${PROJECT_PATH}/.cursor/rules"

GEN_ARGS=(-o "${PROJECT_PATH}/.cursor/qa-skills.lock")
[[ "${INCLUDE_BETA}" == true ]] && GEN_ARGS+=(--include-beta)

python3 "${SCRIPT_DIR}/generate-skills-lock.py" "${GEN_ARGS[@]}"
cp "${QA_ROOT}/templates/qa-project.mdc.example" "${PROJECT_PATH}/.cursor/rules/qa-project.mdc"

"${SCRIPT_DIR}/sync-skills-to-project.sh" "${PROJECT_PATH}"

echo ""
echo "次: ${PROJECT_PATH}/.cursor/qa-profile.yaml の paths を編集"
echo "カタログ: skill-governance/skill-catalog.json / docs/qa-skills-catalog.md"
echo "Done."
