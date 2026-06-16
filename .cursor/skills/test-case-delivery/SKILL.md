---
name: test-case-delivery
description: >-
  テストケースを計画→設計→L4手動ドキュメント→registry トレーサビリティ→カバレッジ算出の順で作成する。
  プロジェクトの TEST_CASE_PLAN.md / registry.json を正とする。全網羅＋ペアワイズ削減。
  テストケース、L4、手動テスト、トレーサビリティ、TC-ID、カバレッジ依頼時に使用する。
metadata:
  version: "1.0.0"
  platform_version: "1"
  changelog_summary: "QA repo へ移行。版管理開始。"
---

# テストケース計画・設計・作成

**計画 → 設計 → ユーザー確認 → registry → L4 → カバレッジ**

## Phase 0（必須）

AskQuestion で確認:

- スコープ: 単体 / +Feature / +E2E
- L4: CLI / 抽象 / **ハイブリッド**

## プロジェクトの正（探索順）

1. `doc/TEST_CASE_PLAN.md`
2. `doc/TEST_CASE_DESIGN.md`
3. `doc/testcases/registry.json`
4. `scripts/test-case-registry.mjs`, `test-case-coverage.mjs`

無ければ jstqb 同構成で新規作成。

## カバレッジ

```bash
node scripts/test-case-registry.mjs
node scripts/test-case-coverage.mjs
```

- 自動化率 = `automationStatus: implemented` / 総 TC-ID
- 全網羅後、冗長組合せはペアワイズで削減（設計書に理由）

## TC-ID

`TC-UT-BE-*` / `TC-UT-FE-*` / `TC-FT-*` / `TC-E2E-*` / `TC-E2E-M*`

## L4 手順書品質（必須）

- **21_結合テスト項目表.md** — KJDD 形式サマリ + §5 詳細（IT-JSTQB-xxx）
- **00_TEST_ENVIRONMENT.md** — 起動・テストアカウント
- **L4_E2E.md** / **L4_FEATURE.md** — 詳細 No. 手順

## 関連

- unit-test-delivery, test-plan-creation, e2e-strategy-delivery
