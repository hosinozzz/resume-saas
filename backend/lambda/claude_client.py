import json
import os
from functools import lru_cache

import anthropic
import boto3

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 8000

# Prompt Cachingを有効化するため定数として保持（変更頻度を最小化）
_SYSTEM_PROMPT = """あなたは日本の転職市場に精通したキャリアコンサルタントです。
提供された履歴書・職務経歴書のテキストを分析し、魅力的にリメイクしてください。

## 出力形式
必ず以下のJSON形式のみを出力してください。マークダウンのコードブロック（```）は使用禁止。

{
  "summary": "プロフィールサマリー（3行、体言止め可）",
  "skills": [
    {"category": "カテゴリ名", "items": ["スキル1", "スキル2"], "level": 0.85}
  ],
  "certifications": [
    {"date": "2023-04", "name": "資格名", "is_top": true}
  ],
  "career": [
    {
      "period": "2020年4月 〜 現在",
      "company": "株式会社〇〇",
      "role": "インフラエンジニア",
      "bullets": ["主な実績・業務内容（箇条書き）"],
      "tags": ["AWS", "Terraform"]
    }
  ],
  "profile": {
    "name": "氏名",
    "kana": "フリガナ",
    "dob": "1990年1月1日",
    "location": "東京都",
    "tel": "090-0000-0000",
    "pr": "自己PR文（150字程度）"
  },
  "meta": {"job_type": "SES", "experience_years": 5}
}

## 改善ルール
- 実績は数値・規模を添えて具体化する（例: 「サーバー移行」→「オンプレ20台をAWS移行、コスト30%削減」）
- スキルのlevelは0.0〜1.0（0.9=上級、0.7=中級、0.5=基礎）
- job_typeはSES技術職なら"SES"、正社員志向なら"正社員"
- 情報が不足している場合は推測せず省略する（空配列・空文字を使用）
- 出力はJSONのみ。説明文・前置き・コードブロック禁止"""


@lru_cache(maxsize=1)
def _get_api_key() -> str:
    # 環境変数に直接APIキーがある場合はそちらを優先（開発・テスト用）
    if direct := os.environ.get("CLAUDE_API_KEY"):
        return direct
    sm = boto3.client("secretsmanager", region_name="ap-northeast-1")
    resp = sm.get_secret_value(SecretId="resume-saas/claude-api-key")
    try:
        return json.loads(resp["SecretString"])["api_key"]
    except (json.JSONDecodeError, KeyError):
        return resp["SecretString"]


@lru_cache(maxsize=1)
def _get_client() -> anthropic.Anthropic:
    # CLAUDE_API_TIMEOUT: mainは25秒（API GW制限）、workerは600秒（非同期処理）
    timeout = float(os.environ.get("CLAUDE_API_TIMEOUT", "600"))
    return anthropic.Anthropic(api_key=_get_api_key(), timeout=timeout)


def improve_resume(resume_text: str) -> dict:
    """履歴書テキストをClaude APIで改善し、JSONデータを返す。"""
    try:
        message = _get_client().messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=[
                {
                    "type": "text",
                    "text": _SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[
                {
                    "role": "user",
                    "content": f"以下の履歴書・職務経歴書を改善してください:\n\n{resume_text}",
                }
            ],
        )
        raw = message.content[0].text.strip()
        # まれにJSONの前後に余分なテキストが付く場合の保険
        if not raw.startswith("{"):
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start >= 0 and end > start:
                raw = raw[start:end]
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Claude APIの出力をJSONとして解析できませんでした: {e}") from e
    except anthropic.APIError as e:
        raise RuntimeError(f"Claude API呼び出しエラー: {e}") from e
