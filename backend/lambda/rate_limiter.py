import os
from datetime import datetime, timezone

import boto3

MAX_REQUESTS = int(os.environ.get("MAX_REQUESTS_PER_HOUR", 3))
TTL_HOURS = 2

_dynamodb = None


def _get_table():
    global _dynamodb
    if _dynamodb is None:
        _dynamodb = boto3.resource("dynamodb", region_name="ap-northeast-1")
    table_name = os.environ.get("DYNAMODB_TABLE_NAME", "resume-saas-rate-limit-prod")
    return _dynamodb.Table(table_name)


def check_rate_limit(ip: str) -> tuple:
    """IPのレート制限をチェック。(allowed, current_count) を返す。"""
    now = datetime.now(timezone.utc)
    pk = f"{ip}#{now.strftime('%Y%m%d%H')}"
    ttl = int(now.timestamp()) + TTL_HOURS * 3600

    try:
        resp = _get_table().update_item(
            Key={"pk": pk},
            UpdateExpression="ADD #cnt :one SET #ttl = if_not_exists(#ttl, :ttl)",
            ExpressionAttributeNames={"#cnt": "count", "#ttl": "ttl"},
            ExpressionAttributeValues={":one": 1, ":ttl": ttl},
            ReturnValues="ALL_NEW",
        )
        count = int(resp["Attributes"]["count"])
        return count <= MAX_REQUESTS, count
    except Exception as e:
        print(f"[WARN] rate_limiter error (allowing request): {e}")
        return True, 0
