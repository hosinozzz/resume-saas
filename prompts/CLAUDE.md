# CLAUDE.md — prompts/

## 役割
Claude APIに渡すシステムプロンプトを管理する。

## 原則
- プロンプトは `.txt` で管理（コードに埋め込まない）
- Prompt Cachingを効かせるため、システムプロンプトは変更頻度を最小に
- 出力は必ず **JSONのみ** を指示する（マークダウンコードブロック禁止）

## プロンプト一覧
| ファイル | 用途 |
|---------|------|
| `ses_specialist.txt` | SES技術職特化の履歴書改善 |
| `regular_employee.txt` | 正社員志向の履歴書改善 |
| `html_template.txt` | HTMLポートフォリオ生成指示 |

## JSON出力スキーマ（Claude APIへの指示）
```json
{
  "summary": "プロフィールサマリー（3行）",
  "skills": [{"category": "", "items": [], "level": 0.0}],
  "certifications": [{"date": "", "name": "", "is_top": false}],
  "career": [{"period": "", "company": "", "role": "", "bullets": [], "tags": []}],
  "profile": {"name": "", "kana": "", "dob": "", "location": "", "tel": "", "pr": ""},
  "meta": {"job_type": "SES|正社員", "experience_years": 0}
}
```
