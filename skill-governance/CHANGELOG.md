# QA Skills v1.0.0

**日付**: 2026-06-16  
**git tag（予定）**: `qa-skills/v1.0.0`

## 含まれる Skills

| Skill | version |
|-------|---------|
| viewpoint-coverage-matrix | 1.0.0 |
| test-plan-creation | 1.0.0 |
| test-case-generation | 1.0.0 |
| test-case-delivery | 1.0.0 |
| unit-test-delivery | 1.0.0 |
| e2e-strategy-delivery | 1.0.0 |
| test-completion-report | 1.0.0 |
| standard-viewpoints-qa | 1.0.0 |
| standard-viewpoints-add-from-request | 1.0.0 |

## 主な変更

- `skill-governance/skill-catalog.json` で tier 管理（distributed / beta / qa-internal）
- setup 既定は **distributed のみ**（現時点: `test-completion-report`）
- `--include-beta` で検証用 Skill を追加
- qa-internal は他プロジェクトへ sync しない

## 配布対象（v1.0.0）

| tier | Skills |
|------|--------|
| distributed | test-completion-report |
| beta | viewpoint-coverage-matrix, test-plan-creation, test-case-*, unit-test-delivery, e2e-strategy-delivery |
| qa-internal | standard-viewpoints-* |

## プロジェクトへ適用

```bash
./scripts/sync-skills-to-project.sh /path/to/project
```

## 既知の制限（Phase 2 以降）

- eval / 週次 monitor 未実装
- `--upgrade` は git tag checkout 未実装（ファイル sync のみ）
- test-case-generation 等は KJDD パスが Skill 本文に残存（profile 化は Phase 4）
