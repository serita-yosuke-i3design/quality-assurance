# プロジェクトプロファイル解決（全 QA Skills 共通）

Phase 0 の最初に実施する。Skill 本文にプロジェクト名・絶対パスをハードコードしない。

## 解決順

1. **`.cursor/qa-profile.yaml`** を Read（sync で配置されたプロファイル。最優先）
2. 無ければ **`.cursor/rules/qa-project.mdc`** の `profile` ID を確認
3. ワークスペースに `quality-assurance` がある場合: `profiles/{profile_id}.yaml` を Read
4. いずれも無ければ **ユーザーにプロジェクト ID または主要パスを1〜2問**

## profile から取るもの

| キー | 用途 |
| --- | --- |
| `paths.*` | 成果物の保存先・参照先 |
| `sources.*` | 要件 CSV・ケース正ソース |
| `conventions.*` | 機能ID 規則・組合せ方針・重点領域 |
| `artifact_metadata` | 成果物ヘッダに追記する Skill 版行 |

## 版の記録

- `.cursor/qa-skills.lock` の `skills.{skill-name}` が pin 版
- Phase C 保存時、成果物 md ヘッダに `**作成 Skill**: {name}@{version}` を追記（profile の `artifact_metadata` 参照）

## 標準観点表

- `standard_viewpoints.repo_relative` から `viewpoints/` を Read
- プロジェクトのみ開いている場合: sync 済み Skill 内 `standard-viewpoints-qa/reference.md` の索引を使うか、multi-root で QA repo を開く
