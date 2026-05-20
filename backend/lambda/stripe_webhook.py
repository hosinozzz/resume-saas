import json
import os

import boto3
import stripe

S3 = boto3.client("s3")
GENERATED_BUCKET = os.environ.get("GENERATED_BUCKET_NAME", "")

CORS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "content-type,stripe-signature",
    "Content-Type": "application/json",
}

_PRESIGN_EXPIRE = 3600  # 1時間


def _get_stripe_key() -> str:
    if key := os.environ.get("STRIPE_SECRET_KEY"):
        return key
    import boto3 as _b
    sm = _b.client("secretsmanager", region_name="ap-northeast-1")
    resp = sm.get_secret_value(SecretId="resume-saas/stripe-keys")
    try:
        return json.loads(resp["SecretString"])["secret_key"]
    except (json.JSONDecodeError, KeyError):
        return resp["SecretString"]


def _get_webhook_secret() -> str:
    if s := os.environ.get("STRIPE_WEBHOOK_SECRET"):
        return s
    import boto3 as _b
    sm = _b.client("secretsmanager", region_name="ap-northeast-1")
    resp = sm.get_secret_value(SecretId="resume-saas/stripe-keys")
    try:
        return json.loads(resp["SecretString"])["webhook_secret"]
    except (json.JSONDecodeError, KeyError):
        return resp["SecretString"]


def create_checkout_session(event: dict) -> dict:
    """Stripe Checkout Sessionを作成して返す。"""
    try:
        raw_body = event.get("body") or "{}"
        try:
            body = json.loads(raw_body)
        except (json.JSONDecodeError, ValueError):
            return _error(400, "リクエストの形式が正しくありません")
        session_id = body.get("sessionId")
        if not session_id:
            return _error(400, "sessionIdが必要です")

        stripe.api_key = _get_stripe_key()

        origin = event.get("headers", {}).get("origin", "https://localhost")
        checkout = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "jpy",
                    "unit_amount": 250,
                    "product_data": {"name": "履歴書リメイク 完全版ダウンロード"},
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=f"{origin}/preview.html?session={session_id}&paid=true",
            cancel_url=f"{origin}/preview.html?session={session_id}",
            metadata={"resume_session_id": session_id},
        )
        return _ok({"checkoutUrl": checkout.url})
    except stripe.StripeError as e:
        print(f"[ERROR] Stripe checkout: {e}")
        return _error(500, "決済の準備中にエラーが発生しました")


def handle_webhook(event: dict) -> dict:
    """Stripe Webhookを受け取り、決済完了後に署名付きURLを返す。"""
    payload = event.get("body", "")
    if event.get("isBase64Encoded"):
        import base64
        payload = base64.b64decode(payload).decode("utf-8")

    sig_header = event.get("headers", {}).get("stripe-signature", "")

    try:
        stripe.api_key = _get_stripe_key()
        stripe_event = stripe.Webhook.construct_event(
            payload, sig_header, _get_webhook_secret()
        )
    except stripe.SignatureVerificationError:
        print("[WARN] Stripe署名検証失敗")
        return _error(400, "署名が無効です")
    except Exception as e:
        print(f"[ERROR] Webhookペイロード解析エラー: {e}")
        return _error(400, "ペイロードが無効です")

    try:
        if stripe_event["type"] == "checkout.session.completed":
            session = stripe_event["data"]["object"]
            # stripe 15.x: StripeObjectは.get()を持たない（__getattr__でKeyError→AttributeError）
            # __getitem__は定義済みなので[]アクセスを使う
            metadata = session["metadata"] if "metadata" in session._data else {}
            if isinstance(metadata, dict):
                resume_session_id = metadata.get("resume_session_id")
            else:
                # StripeObject型のmetadataは[]アクセスで値を取得
                try:
                    resume_session_id = metadata["resume_session_id"]
                except (KeyError, TypeError):
                    resume_session_id = None
            print(f"[INFO] Webhook受信: type={stripe_event['type']}, resume_session_id={resume_session_id}")
            if resume_session_id:
                _fulfill_order(resume_session_id)
    except Exception as e:
        # 処理エラーはログに記録するがStripeには200を返す（リトライ防止）
        print(f"[ERROR] webhook処理エラー: {e}")

    return _ok({"received": True})


def _fulfill_order(resume_session_id: str):
    """クリーン版HTMLの署名付きURLを発行（DynamoDBに保存）。"""
    try:
        clean_url = S3.generate_presigned_url(
            "get_object",
            Params={"Bucket": GENERATED_BUCKET, "Key": f"{resume_session_id}/clean.html"},
            ExpiresIn=_PRESIGN_EXPIRE,
        )
        # DynamoDBに署名付きURLを保存（フロントがポーリングして取得）
        dynamodb = boto3.resource("dynamodb", region_name="ap-northeast-1")
        table = dynamodb.Table(os.environ.get("DYNAMODB_TABLE_NAME", "resume-saas-rate-limit-prod"))
        import time
        table.put_item(Item={
            "pk": f"payment#{resume_session_id}",
            "clean_url": clean_url,
            "ttl": int(time.time()) + _PRESIGN_EXPIRE,
        })
        print(f"[INFO] クリーン版URL発行完了: {resume_session_id}")
    except Exception as e:
        print(f"[ERROR] fulfill_order: {e}")


def get_clean_url(event: dict) -> dict:
    """決済完了後のクリーン版URLを返す（フロントのポーリング用）。"""
    params = event.get("queryStringParameters") or {}
    session_id = params.get("sessionId")
    if not session_id:
        return _error(400, "sessionIdが必要です")

    dynamodb = boto3.resource("dynamodb", region_name="ap-northeast-1")
    table = dynamodb.Table(os.environ.get("DYNAMODB_TABLE_NAME", "resume-saas-rate-limit-prod"))
    resp = table.get_item(Key={"pk": f"payment#{session_id}"})
    item = resp.get("Item")
    if not item:
        return _error(404, "決済情報が見つかりません。しばらくお待ちください。")

    return _ok({"cleanUrl": item["clean_url"]})


def _ok(body: dict) -> dict:
    return {"statusCode": 200, "headers": CORS, "body": json.dumps(body, ensure_ascii=False)}


def _error(status: int, message: str) -> dict:
    return {"statusCode": status, "headers": CORS, "body": json.dumps({"error": message}, ensure_ascii=False)}
