import json
import os
import time

import boto3

from claude_client import improve_resume
from html_generator import generate_portfolio_html, select_template, TEMPLATES
from watermark import add_watermark

S3 = boto3.client("s3")
DYNAMO = boto3.resource("dynamodb")
GENERATED_BUCKET = os.environ["GENERATED_BUCKET_NAME"]
_table = None


def _job_table():
    global _table
    if _table is None:
        _table = DYNAMO.Table(os.environ["DYNAMODB_TABLE_NAME"])
    return _table


def lambda_handler(event, context):
    for record in event.get("Records", []):
        _process_record(record)


def _process_record(record):
    body = json.loads(record["body"])
    job_id = body["job_id"]
    s3_key = body["s3_key"]
    photo_key = body.get("photo_key")

    try:
        _update_job(job_id, {"status": "processing"})

        # S3からパース済み履歴書テキストを取得
        resp = S3.get_object(Bucket=GENERATED_BUCKET, Key=s3_key)
        resume_text = resp["Body"].read().decode("utf-8")

        # 写真データを取得（docxのみ存在）
        photo_b64 = None
        if photo_key:
            try:
                photo_resp = S3.get_object(Bucket=GENERATED_BUCKET, Key=photo_key)
                photo_b64 = photo_resp["Body"].read().decode("utf-8")
            except Exception as e:
                print(f"[WARN] photo fetch failed: {e}")

        # Claude APIで改善してHTMLを生成
        template_id = body.get("template_id", "auto")
        improved_data = improve_resume(resume_text)
        if template_id and template_id != "auto" and template_id in TEMPLATES:
            template = template_id
            print(f"[INFO] using specified template: {template}")
        else:
            template = select_template(improved_data)
            print(f"[INFO] auto-selected template: {template}")
        html_clean = generate_portfolio_html(improved_data, template, photo_b64=photo_b64)
        html_preview = add_watermark(html_clean)

        # S3に保存
        _s3_put(f"{job_id}/preview.html", html_preview)
        _s3_put(f"{job_id}/clean.html", html_clean)

        # プレビュー用署名付きURL（1時間有効）
        preview_url = S3.generate_presigned_url(
            "get_object",
            Params={"Bucket": GENERATED_BUCKET, "Key": f"{job_id}/preview.html"},
            ExpiresIn=3600,
        )

        _update_job(job_id, {
            "status": "done",
            "previewUrl": preview_url,
            "sessionId": job_id,
        })

    except Exception as e:
        print(f"[ERROR] job {job_id} failed: {e}")
        _update_job(job_id, {
            "status": "error",
            "errorMessage": "処理中にエラーが発生しました。再度お試しください。",
        })
        raise  # SQSにDLQへの移動を委ねる


def _update_job(job_id: str, attrs: dict):
    update_expr = "SET " + ", ".join(f"#{k} = :{k}" for k in attrs)
    expr_names = {f"#{k}": k for k in attrs}
    expr_values = {f":{k}": v for k, v in attrs.items()}

    _job_table().update_item(
        Key={"pk": f"job#{job_id}"},
        UpdateExpression=update_expr,
        ExpressionAttributeNames=expr_names,
        ExpressionAttributeValues=expr_values,
    )


def _s3_put(key: str, html: str):
    S3.put_object(
        Bucket=GENERATED_BUCKET,
        Key=key,
        Body=html.encode("utf-8"),
        ContentType="text/html; charset=utf-8",
    )
