---
name: standard-viewpoints-qa
description: >-
  References the company standard test viewpoints when creating test plans or
  test cases. Use when the user mentions 標準観点, 観点表, テスト観点, テスト計画,
  test plan, test case creation, or when generating test cases from feature
  descriptions. When adding viewpoints not in the standard list, outputs
  proposed new viewpoints in the defined format for later merge into the
  standard viewpoint table.
---

# 標準観点表を参照したテスト計画・テストケース作成

## 前提

- 標準観点表は本リポジトリの `viewpoints/` 配下にあり、`viewpoints/{フォルダ名}/{共通|web|アプリ}.md` で格納されている。
- ワークスペースのルートが親リポジトリの場合は、`standard-viewpoint-table/viewpoints/` または ` standard-viewpoint-table/viewpoints/` を参照する。

## 使い方（観点の参照）

1. **対象機能とプラットフォームを特定する**  
   例: 登録・編集機能 / Web → フォルダ `04-登録・編集`、ファイル `共通.md` と `web.md`。

2. **索引で読むファイルを決める**  
   [reference.md](reference.md) の「機能別索引」で、該当するフォルダと「共通・Web・アプリ」の有無を確認する。

3. **該当ファイルを Read で読み込む**  
   必要なのは「共通」＋「web」または「共通」＋「アプリ」の組み合わせ。該当する .md だけを読み、観点一覧の表を取得する。

4. **テスト計画・テストケースに反映する**  
   読み込んだ観点（テスト観点カテゴリ・テスト項目・確認内容）を、漏れなくテスト計画やテストケースに転用する。表の「確認内容・期待値」をそのままテストポイントとして使ってよい。

## 追加観点を標準に戻すとき

テストケース作成時に **標準観点表にない観点** を追加した場合:

- その観点を [examples.md](examples.md) の「追加観点提案」フォーマットに従って出力する。
- 出力には次を含める: 機能（フォルダ名）、共通|web|アプリ、機能 or 表示、テスト観点カテゴリ、テスト項目、確認内容、学び元プロジェクト（任意）、備考（任意）。
- ユーザーはその提案を `proposals/` に保存するか、該当する viewpoints ファイルに手動で反映する。

## 観点ファイルのスタイル（読み書きするときのルール）

- 観点一覧は4列: 機能 or 表示 / テスト観点カテゴリ / テスト項目（観点）/ 確認内容・期待値。
- 編集履歴は各ファイルの **最下部**。1行の形式: 日付 | 変更種別 | 対象観点 | 学び元プロジェクト | 備考。
- 既存の「共通観点（00-共通から移植）」ブロックは維持する。新規観点は機能固有の表に追加する。

## 参照

- 機能別のファイルパス一覧: [reference.md](reference.md)
- 追加観点提案の出力例: [examples.md](examples.md)
