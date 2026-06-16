#!/usr/bin/env bash
# QA Skills をプロジェクトへ版指定 sync する
# 用法:
#   ./scripts/sync-skills-to-project.sh /path/to/project
#   ./scripts/sync-skills-to-project.sh /path/to/project --upgrade viewpoint-coverage-matrix@1.1.0
#   ./scripts/sync-skills-to-project.sh /path/to/project --prune   # lock 外を削除（明示時のみ）
#
# 詳細: docs/qa-skills-platform-handover.md

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
QA_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SKILLS_SRC="${QA_ROOT}/.cursor/skills"
LOCK_EXAMPLE="${QA_ROOT}/templates/qa-skills.lock.example"

usage() {
  echo "Usage: $0 <project-path> [--upgrade skill-name@version] [--prune]" >&2
  exit 1
}

[[ $# -lt 1 ]] && usage

PROJECT_PATH="$(cd "$1" && pwd)"
shift || true

UPGRADE=""
PRUNE=false
while [[ $# -gt 0 ]]; do
  case "$1" in
    --upgrade)
      [[ $# -lt 2 ]] && usage
      UPGRADE="$2"
      shift 2
      ;;
    --prune)
      PRUNE=true
      shift
      ;;
    *)
      usage
      ;;
  esac
done

DEST_SKILLS="${PROJECT_PATH}/.cursor/skills"
LOCK_FILE="${PROJECT_PATH}/.cursor/qa-skills.lock"

mkdir -p "${DEST_SKILLS}"

if [[ ! -d "${SKILLS_SRC}" ]]; then
  echo "WARN: ${SKILLS_SRC} が未作成です。Phase 1 で Skills を移行してください。" >&2
  echo "      現時点では standard-viewpoint-table/.cursor/skills/ を暫定利用します。" >&2
  SKILLS_SRC="${QA_ROOT}/standard-viewpoint-table/.cursor/skills"
fi

if [[ ! -f "${LOCK_FILE}" ]]; then
  echo "初回: qa-skills.lock を作成します"
  mkdir -p "${PROJECT_PATH}/.cursor"
  cp "${LOCK_EXAMPLE}" "${LOCK_FILE}"
fi

# sync 共通リソース
if [[ -d "${SKILLS_SRC}/_shared" ]]; then
  rsync -a --delete "${SKILLS_SRC}/_shared/" "${DEST_SKILLS}/_shared/"
  echo "synced: _shared"
fi

# lock に列挙された Skill のみ sync
sync_skill() {
  local name="$1"
  [[ "${name}" == "_shared" ]] && return 0
  local src="${SKILLS_SRC}/${name}"
  local dest="${DEST_SKILLS}/${name}"
  if [[ -d "${src}" ]]; then
    rsync -a --delete "${src}/" "${dest}/"
    echo "synced: ${name}"
  else
    echo "SKIP (not found): ${name}" >&2
  fi
}

# lock に列挙された Skill のみ sync（python3 で解析。rg/mapfile 非依存）
read_skills_from_lock() {
  python3 -c "
import re
from pathlib import Path
text = Path('${LOCK_FILE}').read_text(encoding='utf-8')
m = re.search(r'^skills:\s*\n((?:[ \t]+[\w-]+:.*\n)+)', text, re.M)
if not m:
    raise SystemExit('skills block not found')
for line in m.group(1).splitlines():
    sm = re.match(r'^[ \t]+([\w-]+):', line)
    if sm:
        print(sm.group(1))
"
}

SKILLS=()
while IFS= read -r line; do
  [[ -n "${line}" ]] || continue
  SKILLS+=("${line}")
done < <(read_skills_from_lock)

if [[ ${#SKILLS[@]} -eq 0 ]]; then
  echo "ERROR: lock に skills が見つかりません: ${LOCK_FILE}" >&2
  exit 1
fi

if [[ -n "${UPGRADE}" ]]; then
  skill_name="${UPGRADE%@*}"
  version="${UPGRADE#*@}"
  echo "upgrade: ${skill_name} -> ${version}"
  # TODO Phase 1: git tag から該当版を checkout して sync
  sync_skill "${skill_name}"
else
  for s in "${SKILLS[@]}"; do
    sync_skill "${s}"
  done

  # lock 外の Skill: 既定は残す（QA repo 未マージ時の消失を防ぐ）。--prune で削除。
  for d in "${DEST_SKILLS}"/*/; do
    [[ -d "${d}" ]] || continue
    base="$(basename "${d}")"
    [[ "${base}" == "_shared" ]] && continue
    found=false
    for s in "${SKILLS[@]}"; do
      if [[ "${s}" == "${base}" ]]; then
        found=true
        break
      fi
    done
    if [[ "${found}" == false ]]; then
      if [[ "${PRUNE}" == true ]]; then
        rm -rf "${DEST_SKILLS}/${base}"
        echo "removed (not in lock): ${base}"
      else
        echo "WARN: kept (not in lock): ${base} — 削除する場合は --prune" >&2
      fi
    fi
  done
fi

# synced_at 更新（簡易: sed 互換のため python 使用）
if command -v python3 >/dev/null 2>&1; then
  python3 - <<PY
from pathlib import Path
from datetime import date
p = Path("${LOCK_FILE}")
text = p.read_text()
today = date.today().isoformat()
if "synced_at:" in text:
    import re
    text = re.sub(r"^synced_at:.*$", f"synced_at: \"{today}\"", text, flags=re.M)
else:
    text += f"\nsynced_at: \"{today}\"\n"
p.write_text(text)
PY
fi

# プロファイルをプロジェクトへ配置
PROFILE_ID="$(python3 -c "
import re
from pathlib import Path
text = Path('${LOCK_FILE}').read_text()
m = re.search(r'^profile:\s*(\S+)\s*$', text, re.M)
print(m.group(1) if m else 'default')
")"
PROFILE_SRC="${QA_ROOT}/profiles/${PROFILE_ID}.yaml"
PROFILE_DEST="${PROJECT_PATH}/.cursor/qa-profile.yaml"
if [[ -f "${PROFILE_SRC}" ]]; then
  mkdir -p "${PROJECT_PATH}/.cursor"
  if [[ ! -f "${PROFILE_DEST}" ]]; then
    cp "${PROFILE_SRC}" "${PROFILE_DEST}"
    echo "profile: ${PROFILE_ID} -> ${PROFILE_DEST}"
  else
    echo "profile: kept existing ${PROFILE_DEST} (lock profile=${PROFILE_ID})"
  fi
else
  echo "WARN: profile not found: ${PROFILE_SRC}" >&2
fi

echo "Done. lock: ${LOCK_FILE}"
