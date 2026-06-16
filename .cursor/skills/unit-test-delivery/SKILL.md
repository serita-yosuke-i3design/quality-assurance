---
name: unit-test-delivery
description: >-
  単体テストを計画→トレーサビリティ確保→実装→カバレッジ評価の順で進める。
  プロジェクトの UNIT_TEST_PLAN.md を正とし UT-ID 体系で管理する。
  単体テスト実装、トレーサビリティマトリクス、PHPUnit/Vitest、カバレッジ評価依頼時に使用する。
metadata:
  version: "1.0.0"
  platform_version: "1"
  changelog_summary: "QA repo へ移行。版管理開始。"
---

# 単体テスト計画・実装（トレーサビリティ付き）

闇雲にテストを書かない。**計画 → ID 付与 → 実装 → 仕様書同期 → 実行確認** の順を守る。

## プロジェクト固有 vs 共通

作業開始時にリポジトリ内を探索し、以下があればそれを**正**とする。

| 探すパス | 役割 |
|---------|------|
| `doc/UNIT_TEST_PLAN.md` | 単体計画・UT-ID・トレーサビリティ |
| `doc/UNIT_TEST_SPEC.md` | テストから読み取れる仕様 |
| `doc/TEST_PLAN.md` | 全体テスト戦略 |

存在しない場合は Phase 1 で新規作成する（jstqb 参照: 同リポジトリ `doc/UNIT_TEST_PLAN.md`）。

## UT-ID 体系（既定）

| プレフィックス | 意味 |
|---------------|------|
| `UT-BE-SVC-xxx` | Backend Service |
| `UT-BE-REQ-xxx` | Backend Request / Validator |
| `UT-FE-xxx` | Frontend 純粋ロジック |

1 ID = 1 観点。テストコードに ID をコメントで付与する。

## 作業フェーズ

### Phase 0: 棚卸し

1. ビジネスロジック（Services, lib/, 純粋関数）を列挙
2. 既存単体テストと突合
3. マトリクスの ✅/❌ 更新
4. 未計画ロジックに UT-ID を採番（**実装前**）

### Phase 1: 計画確定

- In Scope / Out Scope を明示（Controller・薄いラッパーは通常 Out）
- 観点: 「正しく動く」/「誤動作しない」の2分類

### Phase 2: 実装

- 既存テストの命名・配置・mock パターンに合わせる
- Backend: `tests/Unit/`、Frontend: `{module}.test.ts` 同階層

### Phase 3: ドキュメント同期

- 計画書マトリクス ✅
- 逆仕様書（UNIT_TEST_SPEC 相当）更新
- 定量サマリ更新

### Phase 4: 実行

```bash
# プロジェクトの TEST_PLAN / package.json に従う
cd backend && ./vendor/bin/phpunit tests/Unit
cd frontend && npm run test
```

## 品質ゲート

- 計画 ID すべて PASS
- UT-ID なしのテスト追加禁止
- 計画書と逆仕様書が同期

## 第1レスポンス形式（新規依頼時）

```markdown
# 単体テスト — 棚卸し

## 対象ロジック一覧
## 計画 vs 実装（マトリクス）
## 今回追加する UT-ID
## 質問（1〜2個）
```

全文実装はユーザー合意後（test-plan-creation と同様の対話ドリブン）。

## 関連

- test-plan-creation — 全体テスト計画
- test-case-generation — 結合/E2E ケース
- e2e-strategy-delivery — E2E 設計
