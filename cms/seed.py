"""
Seed the local DynamoDB with sample content for development.

Usage:
    cd cms
    source .venv/bin/activate
    python seed.py

Idempotent — skips items that already exist.
"""
import os
import sys

from dotenv import load_dotenv

load_dotenv()

# Ensure the app package is importable
sys.path.insert(0, os.path.dirname(__file__))

import boto3
from app.db import create_table_if_not_exists, get_table

SAMPLE_CATEGORIES = [
    {"slug": "design", "name": "Design", "page_headline": "Design articles", "max_items": 10},
    {"slug": "engineering", "name": "Engineering", "page_headline": "Engineering articles", "max_items": 10},
]

SAMPLE_POSTS = [
    {
        "slug": "hello-world",
        "title": "Hello World",
        "excerpt": "A first post to test the CMS.",
        "blocks": "[]",
        "published": True,
        "theme_mode": "dark",
        "theme_style": "professional",
        "category_slug": "engineering",
    },
    {
        "slug": "design-principles",
        "title": "Design Principles",
        "excerpt": "A sample design post.",
        "blocks": "[]",
        "published": True,
        "theme_mode": "light",
        "theme_style": "minimal",
        "category_slug": "design",
    },
]

SAMPLE_PAGES = [
    {
        "slug": "about",
        "title": "About",
        "blocks": "[]",
        "published": True,
        "theme_mode": "dark",
        "theme_style": "professional",
    },
]


def _put_if_absent(table, pk: str, sk: str, item: dict) -> bool:
    """Write item only if PK+SK doesn't already exist. Returns True if written."""
    try:
        table.put_item(
            Item={"PK": pk, "SK": sk, **item},
            ConditionExpression="attribute_not_exists(PK)",
        )
        return True
    except table.meta.client.exceptions.ConditionalCheckFailedException:
        return False


def main():
    create_table_if_not_exists()
    table = get_table()

    written = 0

    for cat in SAMPLE_CATEGORIES:
        pk = f"CATEGORY#{cat['slug']}"
        if _put_if_absent(table, pk, "METADATA", cat):
            print(f"  Seeded category: {cat['slug']}")
            written += 1
        else:
            print(f"  Skipped (exists): category {cat['slug']}")

    for post in SAMPLE_POSTS:
        pk = f"POST#{post['slug']}"
        if _put_if_absent(table, pk, "METADATA", post):
            print(f"  Seeded post: {post['slug']}")
            written += 1
        else:
            print(f"  Skipped (exists): post {post['slug']}")

    for page in SAMPLE_PAGES:
        pk = f"PAGE#{page['slug']}"
        if _put_if_absent(table, pk, "METADATA", page):
            print(f"  Seeded page: {page['slug']}")
            written += 1
        else:
            print(f"  Skipped (exists): page {page['slug']}")

    print(f"\nDone — {written} item(s) written.")


if __name__ == "__main__":
    main()
