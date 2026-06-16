# QA Skills 利用手順

Skill 一覧・tier: [qa-skills-catalog.md](qa-skills-catalog.md)

---

## 1. ファイル確認

```bash
test -f .cursor/qa-skills.lock \
  && test -f .cursor/qa-profile.yaml \
  && test -f .cursor/skills/test-completion-report/SKILL.md && echo OK || echo SETUP
```

| 結果 | やること |
|------|---------|
| `OK` | [§2 利用](#2-利用) |
| `SETUP` | [§3 初回セットアップ](#3-初回セットアップ) |

---

## 2. 利用

プロジェクトルートを Cursor で開き、Agent で `/test-completion-report` 等を実行。

**配布対象 Skill（tier: distributed）**

| Skill | 概要 |
|-------|------|
| `test-completion-report` | ISO 29119-3 形式のテスト完了レポート作成 |

beta / qa-internal は [カタログ](qa-skills-catalog.md) 参照。

---

## 3. 初回セットアップ

```
workspace/
├── quality-assurance/
└── your-project/
```

```bash
git clone git@github.com:serita-yosuke-i3design/quality-assurance.git

cd quality-assurance
./scripts/setup-qa-skills.sh ../your-project
```

**セットアップ後:** `.cursor/qa-profile.yaml` の `paths` / `sources` を編集。

```bash
cd ../your-project
git add .cursor/
git commit -m "Add QA Skills"
git push
```

---

## 4. Skill 更新

```bash
cd quality-assurance && git pull
./scripts/sync-skills-to-project.sh ../your-project
```

lock の Skill 一覧は `skill-governance/skill-catalog.json` の tier に従う。追加・昇格時は lock を再生成（[カタログ](qa-skills-catalog.md)）。

lock から外した Skill をプロジェクトから消すのは **`--prune` 明示時のみ**（QA repo マージ前の誤削除防止）。

---

## 参考

### トラブルシュート

| 症状 | 対処 |
|------|------|
| Skill が出ない | プロジェクトルートを開く。lock に該当 Skill があるか |
| lock から外した Skill が残る | 既定動作。QA repo マージ後に `--prune` で削除 |
| パスがずれる | `qa-profile.yaml` を編集 |
| beta Skill が欲しい | QA チームに相談。検証用は `setup --include-beta` |

### 関連

- [qa-skills-catalog.md](qa-skills-catalog.md)
- [qa-skills-platform-handover.md](qa-skills-platform-handover.md)
