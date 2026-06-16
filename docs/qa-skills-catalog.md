# QA Skills カタログ

正本: [skill-governance/skill-catalog.json](../skill-governance/skill-catalog.json)

tier の変更・Skill 追加は QA チームが catalog を更新する。

---

## tier 定義

| tier | 意味 | setup 既定 | 手順書 |
|------|------|-----------|--------|
| **distributed** | 他プロジェクトへ配布・利用推奨 | ✅ 含む | getting-started |
| **beta** | 作成中。配布は `--include-beta` 時のみ | オプション | 本書のみ |
| **qa-internal** | quality-assurance リポジトリ専用 | ❌ | 本書のみ |

---

## 一覧

| Skill | tier | 版 | 概要 |
|-------|------|-----|------|
| `test-completion-report` | distributed | 1.0.0 | ISO 29119-3 形式のテスト完了レポート作成 |
| `viewpoint-coverage-matrix` | beta | 1.0.0 | 機能×観点カバレッジ表（4層・作成中） |
| `test-plan-creation` | beta | 1.0.0 | テスト計画書（00 形式） |
| `test-case-generation` | beta | 1.0.0 | テストケース段階生成 |
| `test-case-delivery` | beta | 1.0.0 | テストケース一連作成 |
| `unit-test-delivery` | beta | 1.0.0 | 単体テスト計画〜カバレッジ |
| `e2e-strategy-delivery` | beta | 1.0.0 | E2E 計画・設計書 |
| `standard-viewpoints-qa` | qa-internal | 1.0.0 | 標準観点表参照 |
| `standard-viewpoints-add-from-request` | qa-internal | 1.0.0 | 標準観点表への追加 |

---

## tier 昇格（QA チーム）

1. Skill の品質・profile 対応を確認
2. `skill-catalog.json` の `tier` を更新
3. `CHANGELOG` に記載
4. 配布対象プロジェクトで `setup` または lock 再生成 → sync

```bash
# lock 再生成（distributed のみ）
python3 scripts/generate-skills-lock.py -o /path/to/project/.cursor/qa-skills.lock

# beta も含める（検証用プロジェクト）
python3 scripts/generate-skills-lock.py --include-beta -o /path/to/project/.cursor/qa-skills.lock
./scripts/sync-skills-to-project.sh /path/to/project
```

---

## 関連

- [qa-skills-getting-started.md](qa-skills-getting-started.md) — 利用者向け手順（distributed のみ）
- [qa-skills-platform-handover.md](qa-skills-platform-handover.md) — 設計
