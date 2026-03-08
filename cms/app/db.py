import logging
import os
from typing import Any, Dict, List, Optional

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import BotoCoreError, ClientError

logger = logging.getLogger(__name__)

TABLE_NAME = os.getenv("DYNAMODB_TABLE", "jamesbrannon-content")
REGION = os.getenv("AWS_REGION", "eu-west-2")
ENDPOINT = os.getenv("DYNAMODB_ENDPOINT")  # None in production

# ── Connection (cached per process) ───────────────────────────────────────────

_table = None
_client = None


def get_table():
    global _table
    if _table is None:
        kwargs: Dict[str, Any] = {"region_name": REGION}
        if ENDPOINT:
            kwargs["endpoint_url"] = ENDPOINT
        dynamodb = boto3.resource("dynamodb", **kwargs)
        _table = dynamodb.Table(TABLE_NAME)
    return _table


def get_client():
    global _client
    if _client is None:
        kwargs: Dict[str, Any] = {"region_name": REGION}
        if ENDPOINT:
            kwargs["endpoint_url"] = ENDPOINT
        _client = boto3.client("dynamodb", **kwargs)
    return _client


def _reset_connection_cache() -> None:
    """Reset cached boto3 connections. Call at the start of each test that uses mock_aws."""
    global _table, _client
    _table = None
    _client = None


def create_table_if_not_exists() -> None:
    client = get_client()
    try:
        client.describe_table(TableName=TABLE_NAME)
    except client.exceptions.ResourceNotFoundException:
        client.create_table(
            TableName=TABLE_NAME,
            KeySchema=[
                {"AttributeName": "PK", "KeyType": "HASH"},
                {"AttributeName": "SK", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "PK", "AttributeType": "S"},
                {"AttributeName": "SK", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        logger.info("Created DynamoDB table: %s", TABLE_NAME)
    except (BotoCoreError, ClientError) as exc:
        logger.error("Failed to check/create DynamoDB table: %s", exc)
        raise


def _strip_keys(item: Dict) -> Dict:
    """Remove internal DynamoDB PK/SK from item before returning to caller."""
    return {k: v for k, v in item.items() if k not in ("PK", "SK")}


def list_content(content_type: str) -> List[Dict]:
    try:
        table = get_table()
        response = table.query(
            KeyConditionExpression=Key("PK").eq(f"CONTENT#{content_type}")
        )
        return [_strip_keys(item) for item in response.get("Items", [])]
    except (BotoCoreError, ClientError) as exc:
        logger.error("list_content(%s) failed: %s", content_type, exc)
        raise


def get_content(content_type: str, slug: str) -> Optional[Dict]:
    try:
        table = get_table()
        response = table.get_item(
            Key={"PK": f"CONTENT#{content_type}", "SK": f"SLUG#{slug}"}
        )
        item = response.get("Item")
        return _strip_keys(item) if item else None
    except (BotoCoreError, ClientError) as exc:
        logger.error("get_content(%s, %s) failed: %s", content_type, slug, exc)
        raise


def put_content(content_type: str, data: Dict) -> Dict:
    if "slug" not in data:
        raise ValueError(f"put_content requires 'slug' in data, got: {list(data.keys())}")
    try:
        table = get_table()
        item = {
            "PK": f"CONTENT#{content_type}",
            "SK": f"SLUG#{data['slug']}",
            **data,
        }
        table.put_item(Item=item)
        return data
    except (BotoCoreError, ClientError) as exc:
        logger.error("put_content(%s, slug=%s) failed: %s", content_type, data.get("slug"), exc)
        raise


def delete_content(content_type: str, slug: str) -> None:
    try:
        table = get_table()
        table.delete_item(
            Key={"PK": f"CONTENT#{content_type}", "SK": f"SLUG#{slug}"}
        )
    except (BotoCoreError, ClientError) as exc:
        logger.error("delete_content(%s, %s) failed: %s", content_type, slug, exc)
        raise


# ── Settings (singleton records) ──────────────────────────────────────────────

def get_setting(key: str) -> Optional[Dict]:
    """Get a singleton settings record by key (e.g. 'BRAND', 'SEO')."""
    try:
        table = get_table()
        response = table.get_item(Key={"PK": "SETTINGS", "SK": key})
        item = response.get("Item")
        return _strip_keys(item) if item else None
    except (BotoCoreError, ClientError) as exc:
        logger.error("get_setting(%s) failed: %s", key, exc)
        raise


def put_setting(key: str, data: Dict) -> Dict:
    """Upsert a singleton settings record."""
    try:
        table = get_table()
        item = {"PK": "SETTINGS", "SK": key, **data}
        table.put_item(Item=item)
        return data
    except (BotoCoreError, ClientError) as exc:
        logger.error("put_setting(%s) failed: %s", key, exc)
        raise
