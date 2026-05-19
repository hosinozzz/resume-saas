# CLAUDE.md — terraform/

## 役割
AWSインフラをTerraformで管理する。最小構成・最小コストを厳守。

## 原則
- リソースを追加する前に「本当に必要か？」を問う
- Free tierを最大限活用
- 全リソースにタグ: `Project = "resume-saas"` を付ける

## 変数命名規則
- リソース名: `resume_saas_*`
- 変数: スネークケース

## 禁止事項
- RDS・ElastiCache・ECSは使わない（コスト大）
- マルチAZ構成は不要（個人サービス）
- NATゲートウェイ不要（LambdaはVPC外で動かす）
