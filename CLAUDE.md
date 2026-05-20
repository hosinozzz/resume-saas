# CLAUDE.md — 履歴書リメイクSaaS プロジェクト全体仕様

## プロジェクト概要

アップロードした履歴書ファイルをClaude APIで魅力的にリメイクし、
HTMLポートフォリオ形式でダウンロード提供するミニマムSaaS。

- **ターゲット**: 日本国内の転職者（特にSES・IT系）
- **価格**: 500円/件（ウォーターマークなし完成版）
- **言語**: フロントUI=日本語、コード=英語、コメント=日本語OK

---

## ビジネスルール（変更禁止）

```
✅ あるもの
- ファイルアップロード（docx / pdf / txt）
- Claude APIによる履歴書内容の改善
- HTMLポートフォリオ生成（ダークテーマ、アニメーション付き）
- ウォーターマーク付きプレビュー（無料）
- 500円決済後にクリーン版ダウンロード
- IPベースのレート制限（1時間に3回まで）
- 月間コスト上限アラート → 自動メンテナンスモード移行

❌ 作らないもの（コードが肥大化するため禁止）
- 会員登録 / SNSログイン
- 履歴保存 / マイページ
- プロフィール機能
- AIカスタムオプション（モード選択等）
- 高度な編集UI
- クレジットシステム
- 管理者ダッシュボード
```

---

## アーキテクチャ（AWS最小構成）

```
[ユーザー]
    │ HTTPS
    ▼
[CloudFront] ──→ [S3: 静的フロントエンド]
    │
    ▼
[API Gateway]
    │
    ▼
[Lambda: Python 3.12]
    ├─ ファイルパース (python-docx / pdfplumber)
    ├─ Claude API呼び出し (claude-sonnet-4-6)
    ├─ HTMLポートフォリオ生成
    ├─ ウォーターマーク付与
    ├─ S3一時保存（TTL: 1時間）
    └─ IPレート制限チェック (DynamoDB)
    │
    ▼
[DynamoDB]        [S3: 生成ファイル一時保存]
    └─ IP管理          └─ 署名付きURL発行

[Stripe Webhook]
    └─ 決済完了 → クリーン版署名付きURL発行
```

### AWS月額コスト目安
| サービス | 月額 |
|---------|------|
| S3 + CloudFront | ~$0.50 |
| API Gateway + Lambda | Free tier内 |
| DynamoDB | Free tier内 |
| **合計（AWS）** | **~$1–2** |

> 実際のコストはClaude API使用量が大半。1件あたり約¥20–25。

---

## ディレクトリ構成

```
resume-saas/
├── CLAUDE.md                  ← このファイル（全体仕様）
│
├── terraform/
│   ├── CLAUDE.md              ← Terraform専用指示
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   └── modules/
│       ├── lambda/
│       ├── api_gateway/
│       ├── s3/
│       ├── cloudfront/
│       └── dynamodb/
│
├── backend/
│   ├── CLAUDE.md              ← Lambda/API専用指示
│   ├── lambda/
│   │   ├── handler.py         ← メインエントリ
│   │   ├── parser.py          ← ファイルパース
│   │   ├── claude_client.py   ← Claude API連携
│   │   ├── html_generator.py  ← HTMLポートフォリオ生成
│   │   ├── watermark.py       ← ウォーターマーク処理
│   │   ├── rate_limiter.py    ← IPレート制限
│   │   └── stripe_webhook.py  ← 決済処理
│   └── requirements.txt
│
├── frontend/
│   ├── CLAUDE.md              ← フロントエンド専用指示
│   ├── index.html             ← アップロードUI
│   ├── preview.html           ← プレビュー画面
│   ├── style.css
│   └── app.js
│
├── prompts/
│   ├── CLAUDE.md              ← プロンプト管理専用指示
│   ├── ses_specialist.txt     ← SES技術職特化プロンプト
│   ├── regular_employee.txt   ← 正社員志向プロンプト
│   └── html_template.txt     ← HTMLポートフォリオ生成プロンプト
│
└── .gitignore
```

---

## 技術スタック

| 層 | 技術 |
|---|---|
| IaC | Terraform >= 1.5 |
| Backend | Python 3.12 / AWS Lambda |
| AI | Claude API (`claude-sonnet-4-6`) |
| Frontend | 純粋なHTML / CSS / Vanilla JS（フレームワークなし） |
| 決済 | Stripe（日本円 / JPY） |
| DB | DynamoDB（IPレート管理のみ） |
| CDN | CloudFront + S3 |

---

## Claude API 呼び出し仕様

```python
# モデル: 常にこれを使う
MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 8000

# 1件あたりのトークン目安
# Input:  ~4,000 tokens（ファイル内容 + システムプロンプト）
# Output: ~6,000 tokens（改善済み内容 + HTML）
# コスト目安: 約$0.15/件（¥22円前後）
```

### プロンプト設計方針
- システムプロンプト（prompts/配下）は固定＝Prompt Cachingで90%割引適用
- ユーザーの履歴書テキストのみ毎回送信
- 出力は必ずJSON形式で受け取り、HTMLテンプレートに注入する設計

---

## レート制限仕様（DynamoDB）

```python
# キー設計
pk = f"{ip_address}#{datetime.now().strftime('%Y%m%d%H')}"

# ルール
MAX_REQUESTS_PER_HOUR = 3
TTL = 2時間（DynamoDB自動削除）

# 超過時: HTTP 429 + メッセージ表示
# "1時間あたり3回まで無料でお試しいただけます"
```

---

## 月間コスト上限・自動停止

```python
# CloudWatch Billing Alarm
MONTHLY_COST_LIMIT_USD = 50  # $50超えたら自動停止

# 停止方法: Lambda Concurrency = 0 に設定
# 停止中はメンテナンスページを表示（S3静的）
```

---

## ウォーターマーク仕様

```
無料プレビュー版:
- HTMLの背景に半透明テキスト "PREVIEW - 500円で完全版ダウンロード"
- CSS pointer-events: none で選択不可
- ダウンロードボタン無効化

500円決済後:
- Stripe Webhook受信
- S3署名付きURL（有効期限1時間）発行
- クリーン版HTML送信
```

---

## Stripe 決済フロー

```
1. ユーザーが「500円でダウンロード」ボタン押下
2. Lambda → Stripe Checkout Session作成
3. Stripe決済完了
4. Stripe Webhook → Lambda (stripe_webhook.py)
5. 生成済みHTMLのS3署名付きURL発行
6. ユーザーにメール or リダイレクトでURL送付
   └─ セッションIDで紐付け（DynamoDB一時保存）
```

---

## セキュリティ方針

```
- APIキーは全てAWS Secrets Manager or Lambda環境変数
- .envはgitignore必須
- Stripe Webhook署名検証必須
- S3バケットはパブリックアクセス禁止（署名付きURLのみ）
- CORS: フロントエンドドメインのみ許可
```

---

## .gitignore 必須項目

```
.env
*.tfvars
terraform/.terraform/
terraform/terraform.tfstate*
__pycache__/
*.pyc
.DS_Store
secrets/
```

---

## HTMLポートフォリオ デザイン仕様

> 参考: このプロジェクトで生成済みのportfolio_hoshino_jaewon.html

```
- テーマ: ダークネイビー × サイバーブルー
- フォント: Bebas Neue（見出し）+ Noto Sans JP（本文）+ JetBrains Mono（コード）
- アニメーション: スクロール連動フェードイン、スキルバー
- セクション構成: Hero → Skills → Certs → Career → Profile → Contact
- 印刷対応: @media print でクリーンA4出力
- レスポンシブ: モバイル対応
```

---

## 言語ルール

ユーザー向けの全テキスト（UI、エラーメッセージ、メール文面）は必ず日本語。
コードのコメントも日本語OK。

---

## 開発時の注意事項

1. **Terraformは必ずplanを確認してからapply**
2. **Lambda関数はローカルでpytest通してからデプロイ**
3. **Claude APIのレスポンスは必ずtry-catchで囲む**
4. **DynamoDBのTTLを必ず設定（コスト管理）**
5. **フロントはフレームワーク禁止（バンドルサイズ最小化）**

---

## このプロジェクトの経緯（コンテキスト）

- オーナー: 星野在原（インフラエンジニア、東京在住、日韓バイリンガル）
- 目的: SES面談のポートフォリオ兼副業収入源
- 制約: 退勤後1〜2日で最低限のMVPを構築
- 方針: シンプルに保つ。機能追加より品質維持を優先。

---

*最終更新: 2026-02-14*
*Generated with Claude Sonnet*
