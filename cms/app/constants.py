"""Centralised keys for DynamoDB content types and settings records."""

# Content types (used as DynamoDB PK suffix: CONTENT#{CONTENT_TYPE})
CONTENT_POST = "POST"
CONTENT_PAGE = "PAGE"
CONTENT_PORTFOLIO = "PORTFOLIO"

# Settings keys (used as DynamoDB SK on the SETTINGS partition)
SETTINGS_BRAND = "BRAND"
SETTINGS_SEO = "SEO"
SETTINGS_PROFILE = "PROFILE"
