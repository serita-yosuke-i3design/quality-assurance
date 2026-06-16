# QA Skills プラットフォーム — 全体設計・引き継ぎ書

**リポジトリ**: `git@github.com:serita-yosuke-i3design/quality-assurance.git`  
**最終更新**: 2026-06-16  
**目的**: QA 関連 Skills の **整備・配布・利用・逆流** を4層に分けて設計し、段階的に実装するための単一引き継ぎドキュメント。

---

## 0. 結論（先に読む）

| 問い | 答え |
|------|------|
| まず `quality-assurance` で基盤を作るべきか | **はい。** 正本・版管理・Loop engineering・逆流受付はすべてここ |
| 他プロジェクト（KJDD 等）で使えるか | **使える。** sync + lock + profile で配布 |
| コピーで最新から切り離される問題 | **lock で版を pin。** 明示 upgrade まで方針は変わらない |
| 他プロジェクトの問題を QA に活かせるか | **Issue / eval PR で逆流。** 他 repo への Actions 書込は不要 |
| GitHub Actions は他 repo に触れるか | **read・PR 作成は可能（権限次第）。** 自動 push は非推奨 |

**4層は別問題として進める。** 一気に全部は不要。Phase 0 から順に。

---

## 1. 4層アーキテクチャ

```
┌─────────────────────────────────────────────────────────────┐
│  quality-assurance（工場）                                    │
│                                                              │
│  [整備]  .cursor/skills/          Skills 正本 + 版メタ       │
│  [整備]  skill-governance/        eval / monitor / policy    │
│  [配布]  scripts/sync-skills-*    lock 指定版をプロジェクトへ │
│  [配布]  profiles/                プロジェクト差分（パス等）    │
│  [逆流]  proposals/ + Issue       他プロジェクトからの改善   │
│  [整備]  .github/workflows/       週次 monitor（将来）        │
└──────────────────────────┬──────────────────────────────────┘
                           │ sync（版指定コピー）
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  各プロジェクト repo（KJDD 等・現場）                          │
│                                                              │
│  [利用]  .cursor/skills/          sync で展開された Skills    │
│  [利用]  .cursor/qa-skills.lock    pin された版              │
│  [利用]  .cursor/rules/qa-project  プロファイル ID 指定       │
│  [利用]  成果物 md                  作成 Skill 版をメタ記録   │
│  [逆流]  QA repo へ Issue / PR     問題・eval 候補の送信      │
└─────────────────────────────────────────────────────────────┘
```

| 層 | 何をするか | 正本の場所 | 自律度 |
|----|-----------|-----------|--------|
| **整備** | Skill 作成・改善・eval・陳腐化検知 | QA repo | Loop engineering（人間マージ必須） |
| **配布** | 版指定でプロジェクトへ Skills を届ける | QA repo | sync スクリプト（人間が upgrade 判断） |
| **利用** | プロジェクトで Skill を実行し成果物を作る | 各プロジェクト | Agent + 人間合意（Phase A〜C） |
| **逆流** | 利用中の問題を QA repo に還流 | QA repo（受付） | Issue 起票は人間、改善は半自律 |

---

## 2. 版管理の考え方（pin 運用）

### 2.1 2種類の「版」

| 概念 | 意味 | 更新タイミング |
|------|------|----------------|
| **最新 Skill** | QA repo `main` / git tag | Loop engineering で随時 |
| **pin された Skill** | プロジェクト `qa-skills.lock` に記載 | **人間が明示 upgrade したときのみ** |

### 2.2 Skill 本体の版メタ（SKILL.md frontmatter）

各 Skill の `SKILL.md` に `metadata` を追記する:

```yaml
---
name: viewpoint-coverage-matrix
description: ...
metadata:
  version: "1.0.0"
  platform_version: "1"          # プラットフォーム全体のスキーマ版（破壊的変更時に increment）
  changelog_summary: "初版。KJDD パスは profiles/kjdd.yaml へ分離予定"
---
```

**semver ルール（QA Skills 用）**

| 変更種別 | 版上げ | 例 |
|---------|--------|-----|
| 文言修正・バグ fix（挙動同じ） | PATCH `1.0.1` | typo、参照パス修正 |
| 手順追加（後方互換） | MINOR `1.1.0` | eval 追加、Phase 説明の明確化 |
| 禁止事項追加・Phase 順序変更 | MAJOR `2.0.0` | 「Phase A で md 禁止」を新設 |

git tag: `viewpoint-coverage-matrix/v1.0.0`（Skill 単位）または `qa-skills/v1.0.0`（一括リリース）。

### 2.3 プロジェクト側 lock ファイル

`.cursor/qa-skills.lock`（sync スクリプトが読む）:

```yaml
# 例: templates/qa-skills.lock.example をコピー
platform: quality-assurance
skills:
  viewpoint-coverage-matrix: "1.0.0"
  test-plan-creation: "1.0.0"
synced_at: "2026-06-16"
qa_repo_ref: "main"   # または tag / commit
```

### 2.4 成果物への版記録

Skill で作成・更新した md のヘッダに追記:

```markdown
**作成 Skill**: viewpoint-coverage-matrix@1.0.0
**作成日**: 2026-06-16
```

→ 後から「どの方針で作られたか」が追跡可能。Skill を upgrade しても **既存成果物は再生成不要**（pin している限り）。

---

## 3. 目標ディレクトリ構成（quality-assurance）

```
quality-assurance/
├── README.md
├── docs/
│   └── qa-skills-platform-handover.md    # ★ 本書
│
├── .cursor/skills/                       # ★ Skills 正本（repo ルートに集約）
│   ├── viewpoint-coverage-matrix/
│   ├── test-plan-creation/
│   ├── standard-viewpoints-qa/           # 既存から移動予定
│   └── skill-quality-governor/         # Loop engineering メタ Skill（将来）
│
├── skill-governance/
│   ├── policy.yaml                       # lift 閾値・人間ゲート
│   └── workspace/                        # benchmark / iteration 結果
│
├── profiles/
│   ├── default.yaml
│   └── kjdd.yaml
│
├── fixtures/                             # eval 用固定入力（live プロジェクト非依存）
│   └── kjdd/
│
├── proposals/                            # 他プロジェクトからの改善候補（既存と統合可）
│
├── scripts/
│   └── sync-skills-to-project.sh
│
├── templates/
│   ├── qa-skills.lock.example
│   └── qa-project.mdc.example
│
├── .github/
│   ├── ISSUE_TEMPLATE/skill-feedback.md
│   └── workflows/                        # skill-monitor.yml（Phase 3）
│
└── standard-viewpoint-table/             # 既存（viewpoints 正はここを維持）
    ├── viewpoints/
    └── docs/Skills運用の考え方.md
```

### 現状との差分（移行タスク）

| 現状 | 目標 | Phase |
|------|------|-------|
| Skills が `standard-viewpoint-table/.cursor/skills/` にネスト | repo ルート `.cursor/skills/` へ移動 | 1 |
| テスト系 Skills が `~/.cursor/skills/` のみ | QA repo へ移行 + sync | 1 |
| KJDD パスが Skill 本文に埋め込み | `profiles/kjdd.yaml` へ分離 | 1 |
| eval / monitor なし | `skill-governance/` + workflow | 2〜3 |

---

## 4. 配布（プロジェクトへの届け方）

### 4.1 推奨: sync + lock（コピー思想の進化版）

```bash
# QA repo から実行
./scripts/sync-skills-to-project.sh /path/to/KJDD

# 特定 Skill を新バージョンへ upgrade
./scripts/sync-skills-to-project.sh /path/to/KJDD \
  --upgrade viewpoint-coverage-matrix@1.1.0
```

- **中身はコピー**だが、**lock で版が固定**される
- Cursor は `~/.cursor/skills/` と **プロジェクト `.cursor/skills/`** を discover する
- プロジェクトを開くだけで Skill が使える（sync 済みなら）

### 4.2 プロジェクト初回セットアップ（チェックリスト）

1. `templates/qa-skills.lock.example` → `.cursor/qa-skills.lock`
2. `templates/qa-project.mdc.example` → `.cursor/rules/qa-project.mdc`（profile ID を指定）
3. `./scripts/sync-skills-to-project.sh <project-path>`
4. Cursor でプロジェクトを開き、`/viewpoint-coverage-matrix` 等が使えることを確認
5. 成果物 md に **作成 Skill 版** を記録する運用を開始

### 4.3 代替: git submodule（チーム向け・将来）

```
プロジェクト/.cursor/skills/_qa → submodule → quality-assurance/.cursor/skills/
```

個人運用では sync の方が軽い。チームで版を厳密に揃える段階で検討。

---

## 5. 利用（プロジェクト現場での Skill 実行）

### 5.1 Agent のコンテキスト解決順

```
1. .cursor/rules/qa-project.mdc  → profile ID（例: kjdd）
2. profiles/{id}.yaml（QA repo 参照 or sync 時にコピー）
3. Skill 本文（汎用手順）
4. プロジェクト repo 内の既存テスト資産を Read
```

**Skill 本文にプロジェクト名・パスをハードコードしない。**

### 5.2 標準観点表との関係

- `standard-viewpoint-table/viewpoints/` = **観点の正**（1箇所のみ）
- `standard-viewpoints-qa` Skill = 索引で `viewpoints/` を Read
- `viewpoint-coverage-matrix` Skill = プロジェクト向けカバレッジ表作成（profile でパス解決）

multi-root workspace（開発時のみ）:

```json
{
  "folders": [
    { "path": "KJDD" },
    { "path": "quality-assurance" }
  ]
}
```

---

## 6. 逆流（他プロジェクト → QA repo）

### 6.1 原則

- **他 repo への Actions 書込はしない**
- **QA repo への Issue / PR で受け付ける**
- Loop engineering が QA repo 内で eval → Skill 修正 Draft PR

### 6.2 逆流チャネル

| チャネル | 誰が | 内容 | 自律度 |
|---------|------|------|--------|
| **GitHub Issue** | プロジェクト担当 | 問題・改善要望 | 人間起票 → AI が分類・草案 |
| **proposals/ PR** | プロジェクト担当 | 追加観点・Skill 改善案 | 人間 PR → AI が eval 化検討 |
| **eval ケース PR** | プロジェクト担当 | 再発防止のテストケース | 人間 PR → monitor に組込 |

Issue テンプレ: `.github/ISSUE_TEMPLATE/skill-feedback.md`

### 6.3 GitHub Actions と他 repo の関係

| 操作 | 可能？ | 推奨 |
|------|--------|------|
| QA repo 内で eval 実行 | ✅ | **基本はここだけ** |
| 他 repo を **read**（fixture 取得） | ✅（PAT / 同一 org） | fixtures/ に固定コピー推奨 |
| 他 repo に **PR 作成** | ✅（権限あれば） | **非推奨**（勝手に方針変更） |
| 他 repo から QA repo へ PR | ✅ | **推奨**（逆流の正） |

---

## 7. 整備（Loop engineering）

### 7.1 実行場所

すべて **QA repo 内**。PC / Cursor 常時起動は不要（GitHub Actions）。

### 7.2 ループ

```
eval 実行（with_skill / without_skill）
  → grading（決定論 + LLM judge）
  → benchmark 集計（lift 算出）
  → 異常時: GitHub Issue 作成
  → Improve: Draft PR（SKILL.md 修正）
  → 人間マージ → git tag リリース
  → プロジェクトは lock upgrade を判断（自動ではない）
```

### 7.3 人間ゲート（必須）

| AI 自律 | 人間必須 |
|---------|---------|
| eval 実行・grade・Issue 作成 | SKILL.md マージ |
| 修正 Draft PR 作成 | deprecate / 削除判断 |
| benchmark 保存 | evals.json の方針変更 |
| | プロジェクト lock の upgrade |

### 7.4 閾値（policy.yaml）

```yaml
lift:
  healthy_min: 0.15
  watch_below: 0.15
  deprecate_if_negative_weeks: 2
regression:
  pass_rate_drop_alert: 0.15
improve:
  max_iterations: 3
  require_human_merge: true
```

---

## 8. 実装ロードマップ

### Phase 0: 基盤 scaffold（本 PR / 今ここ）

- [x] 本引き継ぎ書
- [x] `skill-governance/policy.yaml`
- [x] `profiles/default.yaml`, `profiles/kjdd.yaml`
- [x] `templates/`（lock, qa-project rule）
- [x] `scripts/sync-skills-to-project.sh`（profile 同梱 sync 対応）
- [x] Issue テンプレ
- [x] README から本書へのリンク

**完了条件**: 次の担当者が本書だけで Phase 1 に着手できる。 ✅

### Phase 1: 整備 + 配布 + 利用（最小動線）

| # | タスク | 成果物 | 状態 |
|---|--------|--------|------|
| 1.1 | 既存 Skills を repo ルート `.cursor/skills/` へ移動 | 統合された正本 | ✅ |
| 1.2 | `~/.cursor/skills/` のテスト系 Skills を QA repo へ移行 | 9 Skills + `_shared` | ✅ |
| 1.3 | KJDD パスを `profiles/kjdd.yaml` へ分離し Skill から削除 | vcm / test-plan を profile 化 | ✅（他 Skill は Phase 4） |
| 1.4 | KJDD に lock + qa-project.mdc + sync 実行 | `.cursor/skills/` 展開済み | ✅ |
| 1.5 | 各 Skill に `metadata.version: 1.0.0` 付与 | 版管理開始 | ✅ |
| 1.6 | `skill-catalog.json` + tier 配布（既定 distributed のみ） | `generate-skills-lock.py` | ✅ |
| 1.7 | sync: lock 外 Skill は WARN のみ（`--prune` で削除）+ profile 上書き防止 | `sync-skills-to-project.sh` | ✅ |
| 1.8 | git tag `qa-skills/v1.0.0` | 初回リリース | ⬜ コミット後に実施 |

**Skill tier の正本:** `skill-governance/skill-catalog.json`（一覧は [qa-skills-catalog.md](qa-skills-catalog.md)）

- **distributed** — `setup-qa-skills.sh` 既定で配布（現時点: `test-completion-report` のみ）
- **beta** — `--include-beta` 時のみ（検証プロジェクト向け）
- **qa-internal** — QA repo 内のみ。他プロジェクトへ sync しない

**完了条件**: KJDD を開いて `/viewpoint-coverage-matrix` が profile 経由で動く。 ✅（手動確認推奨）

**残タスク**: `standard-viewpoint-table/.cursor/skills/` の旧配置は参照用に残存。整理は任意。git commit / tag / push。

### Phase 2: 整備（eval パイロット）

| # | タスク | 成果物 |
|---|--------|--------|
| 2.1 | `viewpoint-coverage-matrix/evals/evals.json`（2〜3 cases） | 多ターン eval |
| 2.2 | `fixtures/kjdd/` に最小 fixture | live KJDD 非依存 |
| 2.3 | `scripts/validate_phase_a.py` | 決定論チェック |
| 2.4 | 手動 with/without 比較で lift 初回計測 | benchmark.json |

**完了条件**: lift が数値で出る。

### Phase 3: 整備（monitor 自動化）

| # | タスク | 成果物 |
|---|--------|--------|
| 3.1 | `.github/workflows/skill-monitor.yml` | 週次 cron |
| 3.2 | 異常時 Issue 自動作成 | スマホ通知 |
| 3.3 | `skill-quality-governor` メタ Skill | 運用手順の Skill 化 |

**完了条件**: PC オフで週次レポート / 異常 Issue が届く。

### Phase 4: 逆流 + 横展開

| # | タスク | 成果物 |
|---|--------|--------|
| 4.1 | 第2プロジェクト用 `profiles/xxx.yaml` | 横展開実証 |
| 4.2 | skill-feedback Issue 運用開始 | 逆流チャネル |
| 4.3 | 他 Skill へ eval 横展開 | テスト系全体 |

**完了条件**: KJDD 以外で Skill 利用 → 問題 → Issue → Skill 改善 PR の一連が1回通る。

---

## 9. 他リポジトリへ移ったときの引き継ぎ手順

### 9.1 QA repo で作業を再開する場合

```bash
git clone git@github.com:serita-yosuke-i3design/quality-assurance.git
cd quality-assurance
# 本書を読む
open docs/qa-skills-platform-handover.md
# 未完了 Phase のチェックリストを確認（§8）
```

### 9.2 プロジェクト repo（KJDD 等）で Skill を使う場合

```bash
git clone <project-repo>
cd quality-assurance
./scripts/sync-skills-to-project.sh ../KJDD
# KJDD を Cursor で開く
# .cursor/qa-skills.lock の版を確認
```

### 9.3 Skill を更新したあとプロジェクトへ反映

```bash
# QA repo で Skill マージ・tag 後
git tag qa-skills/v1.1.0
./scripts/sync-skills-to-project.sh ../KJDD --upgrade viewpoint-coverage-matrix@1.1.0
# KJDD の lock を確認・コミット
# CHANGELOG を読み、既存成果物への影響を判断
```

### 9.4 問題を QA に還流する場合

1. QA repo で Issue 作成（テンプレ `skill-feedback`）
2. 再現手順・プロジェクト名・使用中 Skill 版（lock から）を記載
3. 可能なら匿名化 fixture を PR

---

## 10. 用語集

| 用語 | 意味 |
|------|------|
| **正本** | 編集する唯一のソース（QA repo） |
| **pin** | プロジェクトが意図的に固定した Skill 版 |
| **lift** | `pass_rate(with_skill) - pass_rate(without_skill)` |
| **fixture** | eval 用の固定入力データ |
| **profile** | プロジェクト固有パス・規約の YAML |
| **逆流** | プロジェクト利用 → QA repo 改善 |
| **Loop engineering** | eval → 改善 → 再 eval の自律サイクル |

---

## 11. 関連ドキュメント

| パス | 内容 |
|------|------|
| [**docs/qa-skills-getting-started.md**](qa-skills-getting-started.md) | **利用手順書（初めての方）** |
| `docs/qa-skills-platform-handover.md` | 本書（設計・引き継ぎ） |
| `standard-viewpoint-table/docs/Skills運用の考え方.md` | 標準観点 × Skill |
| `skill-governance/policy.yaml` | monitor 閾値 |
| `profiles/kjdd.yaml` | KJDD 向けパス・規約 |
| [agentskills.io evaluating skills](https://agentskills.io/skill-creation/evaluating-skills) | eval 標準 |

---

## 12. 変更履歴

| 日付 | 版 | 変更 |
|------|-----|------|
| 2026-06-16 | 1.0 | 初版。4層設計・pin 運用・ロードマップ・引き継ぎ手順 |
