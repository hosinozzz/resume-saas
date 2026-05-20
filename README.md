# ResumeAI — AI 履歴書リメイク SaaS

> 履歴書をアップロードするだけで、Claude AI が魅力的な HTML ポートフォリオに自動変換するミニマム SaaS。

---

## 1. サービスコンセプト

### サービス概要

| 項目 | 内容 |
|------|------|
| **サービス名** | ResumeAI（resumeai.jp） |
| **コンセプト** | 履歴書・職務経歴書を AI でリメイクし、印刷対応 HTML ポートフォリオとして提供 |
| **主な機能** | ファイルアップロード → AI 改善 → HTML 生成 → プレビュー（無料）→ クリーン版ダウンロード（有料） |
| **価格** | ¥500 / 件（オープニングセール中 ¥250） |
| **対応フォーマット** | docx / pdf / txt（最大 3 ファイル同時アップロード） |

### ターゲットユーザー

- **SES・IT 系エンジニア**：面談用ポートフォリオが必要な常駐型エンジニア
- **転職活動中の IT 系人材**：職務経歴書を見栄えよく整えたい層
- **副業・フリーランス志望者**：自己 PR 資料を短時間で仕上げたい層

### ビジネスモデル

```
無料: アップロード → AI 改善 → ウォーターマーク付きプレビュー閲覧
有料: ¥250〜500 の Stripe 決済 → ウォーターマークなし完全版 HTML ダウンロード
```

---

## 2. アーキテクチャ設計

### AWS 構成図

```
[ブラウザ]
    │  HTTPS
    ▼
[CloudFront]  ←── ACM 証明書（us-east-1, resumeai.jp + www）
    │  ├─ CloudFront Function: resumeai.jp → www 301 リダイレクト
    │  ├─ エイリアス: www.resumeai.jp
    │  └─ OAC（Origin Access Control）
    ▼
[S3: resume-saas-frontend-prod]
    └─ 静的ファイル（index.html / preview.html / style.css / app.js）

[ブラウザ]
    │  API コール
    ▼
[API Gateway（HTTP API）]
    │  POST /upload, GET /status/{job_id}
    │  POST /payment/checkout, POST /payment/webhook
    │  GET  /payment/clean-url, POST /contact
    ▼
[Lambda: resume-saas-prod（Python 3.12）]  ←── Secrets Manager（APIキー）
    │  ├─ ファイルパース（python-docx / pypdfium2）
    │  ├─ IP レート制限チェック（1時間3回まで）
    │  ├─ S3 へ原本テキスト保存
    │  └─ SQS へジョブ投入
    │
    ├──[DynamoDB: resume-saas-rate-limit-prod]
    │       └─ IP 管理テーブル + ジョブステータス管理
    │
    └──[SQS: resume-saas-worker-prod]
            │  非同期キュー（DLQ 付き）
            ▼
       [Lambda: resume-saas-worker-prod（Python 3.12）]
            │  ├─ Claude API 呼び出し（claude-sonnet-4-6）
            │  │       Prompt Caching 有効（コスト 90% 削減）
            │  ├─ 職種自動判定 → 6 テンプレートから最適選択
            │  ├─ HTML ポートフォリオ生成（写真埋め込み対応）
            │  ├─ ウォーターマーク付与（プレビュー版）
            │  └─ S3 へ preview.html / clean.html 保存
            │
            └──[S3: resume-saas-generated-prod]
                    ├─ uploaded/{job_id}/resume.txt  （TTL: 1 日）
                    ├─ uploaded/{job_id}/photo.txt   （TTL: 1 日）
                    ├─ {job_id}/preview.html         （TTL: 7 日）
                    └─ {job_id}/clean.html           （TTL: 7 日）

[Stripe Webhook]
    │  checkout.session.completed イベント
    ▼
[Lambda: resume-saas-prod]
    └─ clean.html の署名付き URL を発行（有効期限 1 時間）

[AWS SES] ── お問い合わせメール転送（SES 送信元検証済み）
[CloudWatch + SNS] ── 月額 $50 超過アラーム → SNS 通知

[Route53: resumeai.jp]
    ├─ A/AAAA   resumeai.jp      → CloudFront（alias）
    ├─ A/AAAA   www.resumeai.jp  → CloudFront（alias）
    └─ CNAME    ACM 検証レコード（自動）
```

### 使用技術スタック

| レイヤー | 技術 | バージョン / 詳細 |
|---------|------|------------------|
| **IaC** | Terraform | >= 1.5、モジュール分割構成 |
| **CDN / 配信** | CloudFront + S3 | OAC 方式、PriceClass_200 |
| **カスタムドメイン** | Route53 + ACM | resumeai.jp、TLSv1.2_2021 |
| **エッジ処理** | CloudFront Functions | apex → www 301 リダイレクト |
| **API** | API Gateway（HTTP API） | Lambda プロキシ統合 |
| **バックエンド** | Python 3.12 / AWS Lambda | handler.py + worker.py（2 関数構成） |
| **AI** | Claude API（claude-sonnet-4-6） | Prompt Caching 有効 |
| **ファイルパース** | python-docx、pypdfium2 | docx 写真自動抽出対応 |
| **非同期処理** | SQS + SQS DLQ | 最大受信数 3 回、DLQ 保持 14 日 |
| **データストア** | DynamoDB（オンデマンド） | IP レート制限 + ジョブ管理 |
| **決済** | Stripe Checkout | 日本円（JPY）、Webhook 署名検証 |
| **メール** | AWS SES | お問い合わせフォーム転送 |
| **シークレット管理** | AWS Secrets Manager | Claude API キー、Stripe キー |
| **フロントエンド** | Vanilla HTML / CSS / JS | フレームワークなし、Google Fonts |
| **監視** | CloudWatch Billing Alarm | 月額 $50 超過で SNS 通知 |

---

## 3. 月間コスト

### AWS サービス別コスト（月間）

| サービス | 用途 | 月額目安 |
|---------|------|---------|
| S3（2 バケット） | 静的ファイル配信 + 生成 HTML 一時保存 | ~$0.10 |
| CloudFront | HTTPS 配信、日本含むグローバルエッジ | ~$0.30 |
| API Gateway | HTTP API（100 万リクエストまで無料枠） | $0（無料枠内） |
| Lambda（2 関数） | メイン + ワーカー（月 100 万リクエスト無料） | $0（無料枠内） |
| DynamoDB | オンデマンド（月 25GB / 2.5M 読み書き無料） | $0（無料枠内） |
| SQS | ワーカーキュー（月 100 万メッセージ無料） | $0（無料枠内） |
| SES | お問い合わせメール転送 | ~$0.01 |
| Route53 | ホスティングゾーン（$0.50 / ゾーン） | $0.50 |
| Secrets Manager | API キー 2 件（$0.40 / シークレット） | $0.80 |
| CloudWatch | 課金アラーム（10 アラームまで無料） | $0（無料枠内） |
| ACM | TLS 証明書（CloudFront 利用は無料） | $0 |
| **AWS 合計** | | **~$1.5〜2 / 月** |

### Claude API コスト（従量制）

| トークン種別 | 単価 | 1 件あたり | 月 100 件あたり |
|------------|------|------------|----------------|
| Input（キャッシュ済） | $0.30 / M tokens | ~$0.004 | ~$0.40 |
| Input（非キャッシュ） | $3.00 / M tokens | ~$0.012 | ~$1.20 |
| Output | $15.00 / M tokens | ~$0.09 | ~$9.00 |
| **合計目安** | | **~$0.10〜0.15 / 件（≒¥15〜22）** | **~$10〜15** |

> Prompt Caching（システムプロンプトを `cache_control: ephemeral` でキャッシュ）により、Input コストを最大 90% 削減。

### ドメイン費用

| 項目 | 費用 |
|------|------|
| resumeai.jp 年間更新料 | ~¥1,500 / 年（¥125 / 月） |

### 損益分岐点試算

```
月間 AWS + API 費用: ~¥2,000（固定）+ ¥22 × 件数（変動）
1 件あたり売上: ¥250（セール価格）、Stripe 手数料差引後 ~¥240

損益分岐: 約 10 件 / 月 で黒字転換
```

---

## 4. 処理フロー・ロジック

### メイン処理フロー

```
[1] ファイルアップロード
    ブラウザ → POST /upload（multipart/form-data）
        ├─ IP レート制限チェック（DynamoDB：1時間3回まで）
        ├─ ファイルパース（docx / pdf / txt）
        │       └─ docx の場合: 埋め込み写真を base64 抽出
        ├─ resume.txt を S3 に保存（TTL: 1 日）
        ├─ photo.txt を S3 に保存（base64、TTL: 1 日）
        ├─ DynamoDB にジョブレコード作成（status: "pending"）
        └─ SQS にメッセージ投入 → job_id を即時返却

[2] ポーリング（フロントエンド）
    ブラウザ → GET /status/{job_id}（2 秒間隔、最大 90 秒）
        └─ DynamoDB からステータス取得 → done / processing / error を返却

[3] AI 処理（非同期 Worker）
    SQS トリガー → Lambda Worker 起動
        ├─ S3 から resume.txt 取得
        ├─ S3 から photo.txt 取得（存在する場合）
        ├─ Claude API 呼び出し（claude-sonnet-4-6、Prompt Caching）
        │       └─ 出力: JSON（summary / skills / certifications / career / profile）
        ├─ 職種自動判定 → 6 テンプレートから最適選択
        ├─ HTML ポートフォリオ生成（写真を base64 で埋め込み）
        ├─ ウォーターマーク付与 → preview.html
        ├─ S3 に preview.html / clean.html 保存（TTL: 7 日）
        ├─ preview.html の署名付き URL 発行（有効期限: 1 時間）
        └─ DynamoDB のジョブステータスを "done" に更新

[4] プレビュー表示
    ブラウザ → status: done 確認
        └─ iframe で presigned URL から preview.html を表示（ウォーターマーク表示）

[5] 決済フロー
    ブラウザ → POST /payment/checkout（sessionId 送信）
        └─ Stripe Checkout Session 作成 → checkoutUrl を返却
    ブラウザ → Stripe 決済ページへリダイレクト
    ユーザー決済完了 → Stripe が success_url へリダイレクト
        └─ preview.html?paid=true&sessionId={job_id}

[6] クリーン版ダウンロード
    Stripe → POST /payment/webhook（checkout.session.completed）
        └─ Webhook 署名検証 → clean.html の presigned URL 発行（1 時間有効）
    ブラウザ → GET /payment/clean-url?sessionId={id}（ポーリング）
        └─ presigned URL 取得 → Blob ダウンロード（portfolio_resume.html）
```

### 非同期処理（SQS + Worker Lambda）の設計思想

Claude API の処理時間（10〜60 秒）は API Gateway のタイムアウト（29 秒）を超える場合があるため、**SQS による非同期キューイング**を採用。

```
同期処理（採用しない理由）:
  ブラウザ ──[最大60秒]──→ Lambda ──→ Claude API
                            ↑ API GW 29 秒でタイムアウト → エラー

非同期処理（採用）:
  ブラウザ ─[<1秒]→ Lambda(handler) ─→ SQS ─→ Lambda(worker) ─→ Claude API
                    ↑ job_id を即時返却           ↑ バックグラウンドで最大600秒処理
  ブラウザ ─[2秒ごとにポーリング]─→ GET /status/{job_id}
```

| SQS 設定項目 | 設定値 | 理由 |
|------------|-------|------|
| Visibility Timeout | 600 秒 | Worker 最大処理時間（Claude API 含む） |
| Max Receives | 3 回 | 3 回失敗時に DLQ へ移動 |
| DLQ 保持期間 | 14 日 | 手動調査・再処理用 |
| DynamoDB TTL | 2 時間 | ジョブレコードの自動削除 |

---

## 5. 各システム詳細

### フロントエンド（S3 + CloudFront）

**特徴**: フレームワーク不使用（Vanilla HTML/CSS/JS）。バンドルサイズ最小化・メンテナンス性重視。

```
frontend/
├── index.html    ── アップロード UI、テンプレート選択、サンプル 6 種プレビュー
├── preview.html  ── ジョブポーリング、プレビュー iframe、Stripe 決済フロー
├── contact.html  ── お問い合わせフォーム（SES 経由でメール送信）
├── tokusho.html  ── 特定商取引法に基づく表記
├── privacy.html  ── プライバシーポリシー
├── style.css     ── ダークネイビー × サイバーブルーのグローバルスタイル
├── app.js        ── アップロード処理、ドラッグ&ドロップ、ポーリングロジック
└── sample_*.html ── 6 テンプレートのサンプル（base64 写真埋め込み済み）
```

**デザインシステム**:
- テーマ: ダークネイビー（`#0d1529`）× サイバーブルー（`#00d4ff`）
- フォント: Bebas Neue（見出し）/ Noto Sans JP（本文）/ JetBrains Mono（コード）
- アニメーション: スクロール連動フェードイン、スキルバー、プログレスアニメーション
- レスポンシブ対応・印刷最適化（`@media print` で A4 クリーン出力）

**CloudFront 設定**:

| 項目 | 設定値 |
|------|-------|
| キャッシュポリシー | Managed-CachingOptimized |
| オリジンリクエストポリシー | Managed-CORS-S3Origin |
| プロトコル | redirect-to-https |
| 最低 TLS | TLSv1.2_2021 |
| エッジ関数 | CloudFront Functions（apex リダイレクト） |
| エラーハンドリング | 403 → 200（index.html）SPA ルーティング対応 |

---

### バックエンド（Lambda + API Gateway）

**2 Lambda 構成**:

| 関数 | ファイル | トリガー | タイムアウト | 主な処理 |
|------|---------|---------|------------|---------|
| `resume-saas-prod` | handler.py | API Gateway | 29 秒 | ファイル受付、ステータス確認、決済処理、お問い合わせ |
| `resume-saas-worker-prod` | worker.py | SQS | 600 秒 | Claude API 呼び出し、HTML 生成、S3 保存 |

**API エンドポイント一覧**:

```
POST /upload                ── 履歴書アップロード（multipart/form-data）
GET  /status/{job_id}       ── ジョブステータス確認（ポーリング用）
POST /payment/checkout      ── Stripe Checkout Session 作成
POST /payment/webhook       ── Stripe Webhook 受信（署名検証必須）
GET  /payment/clean-url     ── クリーン版 presigned URL 取得
POST /contact               ── お問い合わせ送信（SES 経由）
GET  /health                ── ヘルスチェック
```

**セキュリティ実装**:
- API キーは AWS Secrets Manager で管理
- Stripe Webhook は `stripe.Webhook.construct_event` で署名検証
- S3 バケットはパブリックアクセス禁止（署名付き URL のみアクセス可）
- IP レート制限: 1 時間に 3 リクエストまで（DynamoDB で管理）
- CORS: `Access-Control-Allow-Origin: *`（API Gateway レベル）

---

### AI 処理（Claude API + テンプレート 6 種）

**Claude API 設定**:

```python
MODEL      = "claude-sonnet-4-6"
MAX_TOKENS = 8000

# Prompt Caching（システムプロンプトをキャッシュしてコスト削減）
system = [{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}]
```

**テンプレート自動選択ロジック**:

| テンプレート ID | デザイン | 対象職種 |
|--------------|---------|---------|
| `dark_tech` | ダーク × サイバーブルー | IT エンジニア、SES、インフラ |
| `business_clean` | ホワイト × ネイビー | 営業、マネージャー、ビジネス系 |
| `minimal_pro` | ミニマル × モノクロ | デザイナー、クリエイター |
| `creative_bold` | ビビッド × グラデーション | Web 系、クリエイティブ職 |
| `medical_care` | ソフトグリーン × ホワイト | 医療・看護・福祉 |
| `academic` | クラシック × ネイビー | 教育・研究・公務員 |

Claude API からの JSON 出力構造:

```json
{
  "summary": "プロフィールサマリー",
  "skills": [{"category": "インフラ", "items": ["AWS", "Terraform"], "level": 0.9}],
  "certifications": [{"date": "2023-04", "name": "AWS SAA", "is_top": true}],
  "career": [{"period": "2020年4月〜現在", "company": "株式会社〇〇", "role": "インフラエンジニア",
              "bullets": ["AWSを用いたインフラ構築"], "tags": ["AWS", "Terraform"]}],
  "profile": {"name": "氏名", "kana": "フリガナ", "dob": "1990年1月1日",
              "location": "東京都", "tel": "090-0000-0000", "pr": "自己PR文"},
  "meta": {"job_type": "SES", "experience_years": 5}
}
```

**写真自動抽出**（docx のみ）:
- `doc.part.rels` から画像 relationship を取得し base64 で HTML に直接埋め込み
- 円形クリップ CSS で各テンプレートのヒーローセクションに表示

**ウォーターマーク**:
- 無料プレビュー版: CSS で半透明オーバーレイ（`pointer-events: none`）
- 決済後: ウォーターマークなしの `clean.html` を署名付き URL（1 時間有効）で提供

---

### 決済（Stripe）

```
POST /payment/checkout
    → Stripe Checkout Session 作成（JPY ¥250、metadata: {session_id: job_id}）
    → checkoutUrl を返却

[Stripe 決済完了]
    → success_url: /preview.html?paid=true&sessionId={job_id}

POST /payment/webhook（checkout.session.completed）
    → Webhook 署名検証
    → clean.html の presigned URL 生成（1 時間有効）
    → DynamoDB に clean_url を保存

GET /payment/clean-url?sessionId={id}
    → DynamoDB から clean_url 取得 → クライアントへ返却
    → Blob ダウンロード（portfolio_resume.html）
```

---

### DNS（Route53 + resumeai.jp）

```
Route53 ホスティングゾーン: resumeai.jp
    ├─ NS  resumeai.jp → awsdns-37.org 他 4 レコード（ドメインレジストラへ設定）
    ├─ A    resumeai.jp      → CloudFront（alias: d20pg6j10067w4.cloudfront.net）
    ├─ AAAA resumeai.jp      → CloudFront（alias）
    ├─ A    www.resumeai.jp  → CloudFront（alias）
    ├─ AAAA www.resumeai.jp  → CloudFront（alias）
    └─ CNAME _xxx.resumeai.jp / _xxx.www.resumeai.jp → ACM 検証レコード（自動）

ACM 証明書（us-east-1）
    └─ resumeai.jp + www.resumeai.jp（DNS 検証・発行済み）

CloudFront Function（viewer-request）
    └─ Host: resumeai.jp → 301 Location: https://www.resumeai.jp{uri}
```

---

### IaC（Terraform）

**モジュール構成**:

```
terraform/
├── main.tf         ── プロバイダー、モジュール呼び出し、Route53、ACM、SES、SNS
├── variables.tf    ── 環境変数定義（region、project_name、environment など）
├── outputs.tf      ── CloudFront URL、API エンドポイント、S3 バケット名など
└── modules/
    ├── s3/         ── バケット、暗号化、ライフサイクル（TTL）、CORS
    ├── cloudfront/ ── ディストリビューション、OAC、バケットポリシー、CloudFront Function
    │   └── functions/apex_redirect.js
    ├── lambda/     ── 2 関数、IAM ロール・ポリシー、Function URL、SQS トリガー
    ├── api_gateway/ ── HTTP API、ルート定義、Lambda 統合、CloudWatch ログ
    ├── dynamodb/   ── テーブル定義、TTL（オンデマンドキャパシティ）
    └── sqs/        ── ワーカーキュー + DLQ
```

**コスト管理**:
- CloudWatch Billing Alarm（月額 $50 超過）→ SNS 通知
- 超過時: Lambda Concurrency = 0 に手動設定してサービス停止
- S3 ライフサイクルルールで生成 HTML を 7 日後に自動削除

---

## 6. ディレクトリ構成

```
resume-saas/
├── README.md
├── CLAUDE.md                        ── プロジェクト全体仕様（AI 向けコンテキスト）
├── .gitignore
│
├── frontend/                        ── 静的ファイル（S3 にデプロイ）
│   ├── CLAUDE.md
│   ├── index.html                   ── アップロード UI + テンプレート選択
│   ├── preview.html                 ── プレビュー + 決済フロー
│   ├── contact.html                 ── お問い合わせフォーム
│   ├── tokusho.html                 ── 特定商取引法に基づく表記
│   ├── privacy.html                 ── プライバシーポリシー
│   ├── style.css                    ── グローバルスタイル（ダークテーマ）
│   ├── app.js                       ── メインスクリプト
│   ├── sample_it.html               ── サンプル: dark_tech テンプレート
│   ├── sample_business.html         ── サンプル: business_clean テンプレート
│   ├── sample_minimal.html          ── サンプル: minimal_pro テンプレート
│   ├── sample_creative.html         ── サンプル: creative_bold テンプレート
│   ├── sample_medical.html          ── サンプル: medical_care テンプレート
│   ├── sample_academic.html         ── サンプル: academic テンプレート
│   └── images/                      ── サンプルカード用プロフィール写真
│
├── backend/
│   ├── CLAUDE.md
│   ├── requirements.txt
│   └── lambda/                      ── Lambda デプロイパッケージ（依存ライブラリ含む）
│       ├── handler.py               ── メイン Lambda エントリーポイント
│       ├── worker.py                ── ワーカー Lambda（SQS トリガー）
│       ├── parser.py                ── ファイルパース（docx / pdf / txt + 写真抽出）
│       ├── claude_client.py         ── Claude API 連携（Prompt Caching）
│       ├── html_generator.py        ── HTML ポートフォリオ生成（6 テンプレート）
│       ├── watermark.py             ── ウォーターマーク付与
│       ├── rate_limiter.py          ── IP レート制限（DynamoDB）
│       └── stripe_webhook.py        ── Stripe 決済処理・Webhook 検証
│
├── terraform/
│   ├── CLAUDE.md
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   └── modules/
│       ├── s3/
│       ├── cloudfront/
│       │   └── functions/
│       │       └── apex_redirect.js ── apex リダイレクト CloudFront Function
│       ├── lambda/
│       ├── api_gateway/
│       ├── dynamodb/
│       └── sqs/
│
└── prompts/                         ── Claude API システムプロンプト管理
    └── CLAUDE.md
```

---

## 7. 今後の課題・改善点

### 機能面

| 優先度 | 課題 | 対応方針 |
|-------|------|---------|
| 高 | `resumeai.jp` apex の CloudFront CNAME コンフリクト解消 | 別アカウント保有の CNAME を AWS サポート経由でクリア後、`terraform apply` |
| 高 | Stripe Webhook の冪等性保証 | `stripe_session_id` をキーに DynamoDB で処理済みチェックを追加 |
| 中 | エラー時のユーザー通知改善 | SQS DLQ 着弾時に SES でメール通知を実装 |
| 中 | 複数ページ PDF 対応 | pypdfium2 の全ページテキスト結合（現在は先頭ページのみ抽出） |
| 低 | xlsx / pptx 形式対応 | openpyxl、python-pptx でのパーサー追加 |

### インフラ面

| 優先度 | 課題 | 対応方針 |
|-------|------|---------|
| 高 | Terraform ステートの S3 バックエンド移行 | `main.tf` の `backend "s3"` ブロックのコメントを解除して移行 |
| 中 | Lambda のコールドスタート対策 | Provisioned Concurrency の検討（コスト増とのトレードオフ） |
| 中 | CloudFront キャッシュ無効化の自動化 | デプロイスクリプトに `create-invalidation` を組み込み |
| 低 | マルチリージョン対応 | 現状は ap-northeast-1 のみ。海外展開時に検討 |

### ビジネス面

| 優先度 | 課題 | 対応方針 |
|-------|------|---------|
| 中 | SEO 対応 | OGP タグ、sitemap.xml、robots.txt の整備 |
| 中 | 計測基盤の整備 | Google Analytics または Cloudflare Web Analytics の導入 |
| 低 | 生成完了メール通知 | 結果 URL をメール送信（SES）→ 離脱ユーザーの回収 |
| 低 | プロモーション機能 | クーポンコード対応（Stripe Coupon API） |

---

## デプロイ手順

### 前提条件

- AWS CLI 設定済み（`ap-northeast-1` アクセス権限）
- Terraform >= 1.5
- Python 3.12

### インフラデプロイ

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

### フロントエンドデプロイ

```bash
aws s3 sync frontend/ s3://resume-saas-frontend-prod/ --delete
aws cloudfront create-invalidation --distribution-id E1AXFPG76FJAYV --paths "/*"
```

### Lambda デプロイ

```bash
cd terraform
terraform apply -target=module.lambda
```

### 必要なシークレット（AWS Secrets Manager）

```
resume-saas/claude-api-key  → {"api_key": "sk-ant-..."}
resume-saas/stripe-keys     → {"secret_key": "sk_live_...", "webhook_secret": "whsec_..."}
```

---

## ライセンス

MIT License — Copyright (c) 2026 星野在原

---

*Built with [Claude Code](https://claude.ai/code) · AWS · Stripe · Anthropic Claude API*
