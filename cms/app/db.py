import os
from typing import Any, Dict, List, Optional

import boto3
from boto3.dynamodb.conditions import Key

TABLE_NAME = os.getenv("DYNAMODB_TABLE", "jamesbrannon-content")
REGION = os.getenv("AWS_REGION", "eu-west-2")
ENDPOINT = os.getenv("DYNAMODB_ENDPOINT")  # None in production


def get_table():
    kwargs: Dict[str, Any] = {"region_name": REGION}
    if ENDPOINT:
        kwargs["endpoint_url"] = ENDPOINT
    dynamodb = boto3.resource("dynamodb", **kwargs)
    return dynamodb.Table(TABLE_NAME)


def get_client():
    kwargs: Dict[str, Any] = {"region_name": REGION}
    if ENDPOINT:
        kwargs["endpoint_url"] = ENDPOINT
    return boto3.client("dynamodb", **kwargs)


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
        print(f"Created DynamoDB table: {TABLE_NAME}")


def _strip_keys(item: Dict) -> Dict:
    """Remove internal DynamoDB PK/SK from item before returning to caller."""
    return {k: v for k, v in item.items() if k not in ("PK", "SK")}


def list_content(content_type: str) -> List[Dict]:
    table = get_table()
    response = table.query(
        KeyConditionExpression=Key("PK").eq(f"CONTENT#{content_type}")
    )
    return [_strip_keys(item) for item in response.get("Items", [])]


def get_content(content_type: str, slug: str) -> Optional[Dict]:
    table = get_table()
    response = table.get_item(
        Key={"PK": f"CONTENT#{content_type}", "SK": f"SLUG#{slug}"}
    )
    item = response.get("Item")
    return _strip_keys(item) if item else None


def put_content(content_type: str, data: Dict) -> Dict:
    table = get_table()
    item = {
        "PK": f"CONTENT#{content_type}",
        "SK": f"SLUG#{data['slug']}",
        **data,
    }
    table.put_item(Item=item)
    return data


def delete_content(content_type: str, slug: str) -> None:
    table = get_table()
    table.delete_item(
        Key={"PK": f"CONTENT#{content_type}", "SK": f"SLUG#{slug}"}
    )


# ── Settings (singleton records) ──────────────────────────────────────────────

def get_setting(key: str) -> Optional[Dict]:
    """Get a singleton settings record by key (e.g. 'BRAND', 'HOMEPAGE')."""
    table = get_table()
    response = table.get_item(Key={"PK": "SETTINGS", "SK": key})
    item = response.get("Item")
    return _strip_keys(item) if item else None


def put_setting(key: str, data: Dict) -> Dict:
    """Upsert a singleton settings record."""
    table = get_table()
    item = {"PK": "SETTINGS", "SK": key, **data}
    table.put_item(Item=item)
    return data
