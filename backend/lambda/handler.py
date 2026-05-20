import base64
import json
import os
import time
import uuid

import boto3

from parser import parse_resume

S3 = boto3.client("s3")
SQS = boto3.client("sqs")
DYNAMO = boto3.resource("dynamodb")
GENERATED_BUCKET = os.environ["GENERATED_BUCKET_NAME"]
SQS_QUEUE_URL = os.environ.get("SQS_QUEUE_URL", "")
_table = None

CORS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "content-type,stripe-signature",
    "Content-Type": "application/json",
}


def _job_table():
    global _table
    if _table is None:
        _table = DYNAMO.Table(os.environ["DYNAMODB_TABLE_NAME"])
    return _table


def lambda_handler(event, context):
    method = event.get("requestContext", {}).get("http", {}).get("method", "")
    path = event.get("rawPath", "")

    if method == "OPTIONS":
        return {"statusCode": 200, "headers": CORS, "body": ""}

    try:
        if path == "/upload" and method == "POST":
            return _handle_upload(event)
        elif path.startswith("/status/") and method == "GET":
            return _handle_status(event)
        elif path == "/payment/checkout" and method == "POST":
            from stripe_webhook import create_checkout_session
            return create_checkout_session(event)
        elif path == "/payment/webhook" and method == "POST":
            from stripe_webhook import handle_webhook
            return handle_webhook(event)
        elif path == "/payment/clean-url" and method == "GET":
            from stripe_webhook import get_clean_url
            return get_clean_url(event)
        elif path == "/health":
            return _ok({"status": "ok"})
        else:
            return _error(404, "エンドポイントが見つかりません")
    except Exception as e:
        print(f"[ERROR] unhandled: {e}")
        return _error(500, "サーバーエラーが発生しました。しばらくしてから再度お試しください。")


def _handle_upload(event):
    raw_body = event.get("body", "")
    if event.get("isBase64Encoded"):
        raw_body = base64.b64decode(raw_body)
    elif isinstance(raw_body, str):
        raw_body = raw_body.encode()

    headers = {k.lower(): v for k, v in event.get("headers", {}).items()}
    content_type = headers.get("content-type", "")

    if "multipart/form-data" not in content_type:
        return _error(400, "multipart/form-data 形式で送信してください。")

    file_entries = _extract_multipart_files(raw_body, content_type)
    if not file_entries:
        return _error(400, "ファイルが見つかりません。file_0 フィールドにファイルを添付してください。")

    # 各ファイルのテキスト抽出 → ラベル付きで結合
    sections = []
    for entry in file_entries:
        text = parse_resume(entry["body"], entry["content_type"], entry["filename"])
        if text and text.strip():
            sections.append(f"【{entry['label']}】\n{text.strip()}")

    resume_text = "\n\n".join(sections)
    if len(resume_text.strip()) < 50:
        return _error(400, "ファイルの内容を読み取れませんでした。docx・pdf・xlsx・txt形式のファイルをお試しください。")

    job_id = str(uuid.uuid4())
    text_key = f"uploaded/{job_id}/resume.txt"

    S3.put_object(
        Bucket=GENERATED_BUCKET,
        Key=text_key,
        Body=resume_text.encode("utf-8"),
        ContentType="text/plain; charset=utf-8",
    )

    _job_table().put_item(Item={
        "pk": f"job#{job_id}",
        "status": "pending",
        "ttl": int(time.time()) + 7200,
    })

    SQS.send_message(
        QueueUrl=SQS_QUEUE_URL,
        MessageBody=json.dumps({"job_id": job_id, "s3_key": text_key}),
    )

    return _ok({"jobId": job_id})


def _handle_status(event):
    path = event.get("rawPath", "")
    parts = path.strip("/").split("/")
    if len(parts) < 2 or not parts[1]:
        return _error(400, "job_idが指定されていません。")

    job_id = parts[1]

    try:
        resp = _job_table().get_item(Key={"pk": f"job#{job_id}"})
        item = resp.get("Item")
    except Exception as e:
        print(f"[ERROR] DynamoDB get_item failed: {e}")
        return _error(500, "サーバーエラーが発生しました。")

    if not item:
        return _error(404, "指定されたジョブが見つかりません。")

    status = item.get("status", "pending")

    if status == "done":
        return _ok({
            "status": "done",
            "previewUrl": item.get("previewUrl", ""),
            "sessionId": item.get("sessionId", job_id),
        })
    elif status == "error":
        return _ok({
            "status": "error",
            "message": item.get("errorMessage", "処理中にエラーが発生しました。"),
        })
    else:
        return _ok({"status": status})


def _extract_multipart_files(body: bytes, content_type: str) -> list:
    """
    multipart/form-data から file_N / label_N ペアを最大3件抽出する。
    Returns: [{"body": bytes, "content_type": str, "filename": str, "label": str}, ...]
    """
    boundary = None
    for part in content_type.split(";"):
        part = part.strip()
        if part.lower().startswith("boundary="):
            boundary = part[9:].strip('"')
            break
    if not boundary:
        return []

    files: dict[str, dict] = {}   # index str -> file info
    labels: dict[str, str] = {}   # index str -> label

    delimiter = f"--{boundary}".encode()
    for segment in body.split(delimiter)[1:]:
        if segment.startswith(b"--"):
            break
        if b"\r\n\r\n" not in segment:
            continue

        header_block, content = segment.split(b"\r\n\r\n", 1)
        header_text = header_block.decode("utf-8", errors="replace")

        # Content-Disposition からフィールド名を取得
        field_name = ""
        for line in header_text.split("\r\n"):
            if line.lower().startswith("content-disposition:"):
                for token in line.split(";"):
                    token = token.strip()
                    if token.lower().startswith("name="):
                        field_name = token[5:].strip('"')

        if not field_name:
            continue

        if field_name.startswith("file_"):
            idx = field_name[5:]
            file_ct = "application/octet-stream"
            filename = ""
            for line in header_text.split("\r\n"):
                ll = line.lower()
                if ll.startswith("content-type:"):
                    file_ct = line.split(":", 1)[1].strip()
                if "filename=" in ll:
                    for token in line.split(";"):
                        token = token.strip()
                        if token.lower().startswith("filename="):
                            filename = token[9:].strip('"')
            files[idx] = {
                "body": content.rstrip(b"\r\n"),
                "content_type": file_ct,
                "filename": filename,
            }

        elif field_name.startswith("label_"):
            idx = field_name[6:]
            labels[idx] = content.rstrip(b"\r\n").decode("utf-8", errors="replace").strip()

    result = []
    for idx in sorted(files.keys()):
        entry = dict(files[idx])
        entry["label"] = labels.get(idx, "その他")
        result.append(entry)

    return result[:3]  # 最大3件


def _ok(body: dict):
    return {"statusCode": 200, "headers": CORS, "body": json.dumps(body, ensure_ascii=False)}


def _error(status: int, message: str):
    return {"statusCode": status, "headers": CORS, "body": json.dumps({"error": message}, ensure_ascii=False)}
