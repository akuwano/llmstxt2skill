# CLAUDE.md


## プロダクトビジョンと目的

**ビジョン**

**目的**
llms.txtをskillとしてジェネレートする

---

## ターゲットユーザーと課題・ニーズ

### ターゲットユーザー

### 課題
| 優先度 | 課題 |
|--------|------|
| P0 | |

### ニーズ

---

## 成功の定義


---

## ユーザーストーリー


---

## 機能要件

### 既存機能（実装済み）

| 機能 | モジュール | 説明 |
|------|-----------|------|
| llms.txt取得 | fetcher.py | URLからllms.txtをfetch |
| llms.txtパース | parser.py | H1/blockquote/H2/リンク抽出 |
| Skill生成 | generator.py | LlmsTxt→Skill変換 |
| ファイル出力 | writer.py | ~/.claude/skills/へ出力 |
| CLI | cli.py | コマンドラインインターフェース |

### 新規機能（MVP必須）

| 機能 | 説明 | 状態 |
|------|------|------|
| URL取得 | httpxでllms.txt取得 | 完了 |
| パース | llms.txt形式をパース | 完了 |
| 変換 | Claude Skill形式に変換 | 完了 |
| 出力 | SKILL.mdファイル出力 | 完了 |
| CLI | --dry-run, --force, --name | 完了 |

### 機能の依存関係


---

## 非機能要件

### スケール要件

### 運用要件

---

## 受け入れ条件

### MVP完了の定義

### 品質目標（MVP後）

| 指標 | 目標 | 計測開始 |
|------|------|----------|
| テストカバレッジ | 80%以上 | MVP後 |
| CI実行時間 | 5分以内 | MVP後 |
| スキーマ変換エラー率 | 0% | MVP後 |

---

## 優先順位

| 優先度 | 機能 | 状態 |
|--------|------|------|

---

## Common Commands

```bash
# テスト実行
uv run pytest tests/ -v

# リンター
uv run ruff check src/ tests/

# CLI実行（dry-run）
uv run llmstxt2skill https://docs.databricks.com/llms.txt --dry-run

# CLI実行（実際に出力）
uv run llmstxt2skill https://docs.databricks.com/llms.txt

# 強制上書き
uv run llmstxt2skill https://docs.databricks.com/llms.txt --force

# カスタム名指定
uv run llmstxt2skill https://docs.databricks.com/llms.txt --name databricks
```

---

## Architecture

### Key directories

```
src/llmstxt2skill/
├── cli.py          # CLIエントリーポイント
├── fetcher.py      # URL取得（httpx）
├── parser.py       # llms.txtパース
├── generator.py    # Skill生成
├── writer.py       # ファイル出力
└── models.py       # データクラス
```

### Core modules
| モジュール | 役割 |
|-----------|------|
| models.py | LlmsTxtLink, LlmsTxtSection, LlmsTxt, Skill dataclass |
| parser.py | llms.txt→LlmsTxt変換 |
| generator.py | LlmsTxt→Skill変換、kebab-case変換 |
| fetcher.py | 非同期URL取得 |
| writer.py | SKILL.mdファイル出力 |
| cli.py | argparse、メイン処理 |

---

## Development Workflow

---

## 実装ガイドライン

### 開発哲学

| 原則 | 説明 |
|------|------|
| 段階的な進行 | 一度に大きな変更を行わず、小さな確実なステップで前進する |
| TDD厳守 | Red→Green→Refactorサイクルを必ず守る |
| Tidy First | 機能変更の前にまずコードを整理する |
| 詳細な文書化 | 変更の理由と目的を常に記録する |
| 継続的な検証 | 各ステップで動作を確認し、問題を早期発見する |

### 技術スタック

| カテゴリ | 技術 |
|----------|------|
| 言語 | Python 3.11+ |

### コミット規約

Conventional Commits形式を採用：

```
<type>(<scope>): <description>

# 例
feat(spark): add map field support to ProtoToSparkConverter
fix(dlt): handle empty expectation list
refactor(unity): extract SQL generation to separate method
test(schema): add nested message conversion tests
docs(readme): update architecture diagram
chore(deps): update protobuf to 4.25.0
```

| type | 用途 |
|------|------|
| feat | 新機能 |
| fix | バグ修正 |
| refactor | リファクタリング |
| test | テスト追加・修正 |
| docs | ドキュメント |
| chore | その他（依存関係更新等） |

### TDDサイクル

各機能は以下のサイクルで実装する：

```
1. Red: 失敗するテストを書く
   - 期待する動作を明確に定義
   - 具体的な入力と期待される出力を示す
   - エッジケースと制約条件を明示

2. Green: 最小限の実装でテストを通す
   - 最もシンプルな実装を選択
   - 複雑な最適化は後回し
   - 動作することを最優先

3. Refactor: コードを改善する
   - テストが通る状態を維持
   - 一度に一つの改善に集中
   - リファクタリングの目的を明確に
```

### Tidy First（Kent Beck）

機能変更の前に、まずコードを整理（tidy）する。

#### 適用タイミング

| 状況 | アクション |
|------|----------|
| 変更対象のコードが読みにくい | Tidy First |
| 変更が簡単にできる状態 | そのまま実装 |
| Tidyingのコストが高すぎる | 機能変更後に検討 |

#### Tidyingパターン

| パターン | 説明 |
|----------|------|
| Guard Clauses | ネストを減らすために早期リターンを使う |
| Dead Code | 使われていないコードを削除 |
| Normalize Symmetries | 似た処理は同じ形式で書く |
| Extract Helper | 再利用可能な部分を関数に抽出 |
| One Pile | 散らばった関連コードを一箇所にまとめる |
| Explaining Comments | 理解しにくい箇所にコメントを追加 |
| Explaining Variables | 複雑な式を説明的な変数に分解 |

#### 重要なルール

- 構造的変更と機能的変更を分離する（tidyingは別コミット）
- 小さく整理してから変更する
- 読みやすさを優先（未来の自分のために）

### イテレーション単位

各機能を最小単位に分割し、1イテレーションで1つの機能を完成させる。

#### イテレーションの条件

- **独立して動作可能**: そのステップだけで価値を提供できる
- **検証可能**: テストで動作を具体的に確認できる
- **完結している**: 中途半端な状態で終わらない
- **1コミット**: 1イテレーション = 1コミット

