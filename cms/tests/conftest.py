import os

import boto3
import pytest
from fastapi.testclient import TestClient
from moto import mock_aws

# Must be set before any app imports so db.py picks them up
os.environ.setdefault("AWS_ACCESS_KEY_ID", "testing")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "testing")
os.environ.setdefault("AWS_DEFAULT_REGION", "eu-west-2")
os.environ.setdefault("AWS_REGION", "eu-west-2")
os.environ.setdefault("DYNAMODB_TABLE", "test-jamesbrannon-content")
os.environ.setdefault("ADMIN_USER", "admin")
os.environ.setdefault("ADMIN_PASS", "testpass")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("S3_BUCKET", "test-media")
os.environ.setdefault("S3_BUCKET_REGION", "eu-west-2")
# Force empty — tests use moto which intercepts at the SDK level.
# An explicit endpoint_url would bypass moto and try to connect to MinIO/real AWS.
os.environ["S3_ENDPOINT_URL"] = ""
os.environ["S3_PUBLIC_BASE_URL"] = ""

TABLE_NAME = "test-jamesbrannon-content"


@pytest.fixture()
def aws_mock():
    """Start moto AWS mock, create the DynamoDB table and S3 bucket."""
    from app.db import _reset_connection_cache
    _reset_connection_cache()
    with mock_aws():
        dynamodb = boto3.resource("dynamodb", region_name="eu-west-2")
        dynamodb.create_table(
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
        s3 = boto3.client("s3", region_name="eu-west-2")
        s3.create_bucket(
            Bucket="test-media",
            CreateBucketConfiguration={"LocationConstraint": "eu-west-2"},
        )
        yield


@pytest.fixture()
def client(aws_mock):
    """FastAPI TestClient with mocked DynamoDB."""
    from app.main import app
    return TestClient(app, raise_server_exceptions=True)


# ── Seed helpers ──────────────────────────────────────────────────────────────

def make_post(**kwargs) -> dict:
    defaults = {
        "slug": "test-post",
        "title": "Test Post",
        "blocks": "[]",
        "published": True,
        "theme_mode": "dark",
        "theme_style": "professional",
    }
    return {**defaults, **kwargs}


def make_page(**kwargs) -> dict:
    defaults = {
        "slug": "about",
        "title": "About",
        "blocks": "[]",
        "published": True,
        "theme_mode": "dark",
        "theme_style": "professional",
    }
    return {**defaults, **kwargs}


def make_category(**kwargs) -> dict:
    defaults = {
        "slug": "design",
        "name": "Design",
        "page_headline": "Design articles",
        "max_items": 10,
    }
    return {**defaults, **kwargs}


