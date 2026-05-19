# CLAUDE.md — backend/

## 役割
Lambda（Python 3.12）でファイルパース・Claude API呼び出し・HTML生成・決済処理を担う。

## 原則
- 1 Lambda関数に詰め込まない。ファイルは機能別に分割済み
- Claude APIは必ずtry-catchで囲む
- レスポンスは常にJSON形式

## Claude API
- モデル: `claude-sonnet-4-20250514`（変更禁止）
- システムプロンプトは `../prompts/` から読み込む
- Prompt Cachingを有効化してコスト削減

## エラーレスポンス形式
```json
{"success": false, "error": "メッセージ", "code": "ERROR_CODE"}
```

## 環境変数（Lambda）
- `CLAUDE_API_KEY`
- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `S3_BUCKET_NAME`
- `DYNAMODB_TABLE_NAME`
