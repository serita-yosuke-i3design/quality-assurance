## Quality Assurance

QA 基準・テンプレート・Agent Skills の管理リポジトリ。

| ドキュメント | 内容 |
|-------------|------|
| [利用手順](docs/qa-skills-getting-started.md) | 他プロジェクト向け（**distributed** のみ） |
| [Skill カタログ](docs/qa-skills-catalog.md) | 全 Skill・tier 定義（QA チーム向け） |

```bash
cd quality-assurance
./scripts/setup-qa-skills.sh ../your-project
```

| 領域 | パス |
|------|------|
| Skill カタログ（正本） | `skill-governance/skill-catalog.json` |
| Skills 管理元 | `.cursor/skills/` |
| 初回セットアップ | `scripts/setup-qa-skills.sh` |
| Skill 更新 | `scripts/sync-skills-to-project.sh` |
