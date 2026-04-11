"""
Tests for Pydantic models — validation, defaults, and enum values.
"""
import pytest
from pydantic import ValidationError

from app.models import (
    BrandSettings,
    BlogPageSettings,
    BlogSettings,
    Category,
    ExperienceItem,
    ExperienceSection,
    OGType,
    Page,
    Post,
    ProfileSettings,
    SeoSettings,
    StrengthItem,
    StrengthsSection,
    ThemeMode,
    ThemeStyle,
)


# ── Post ──────────────────────────────────────────────────────────────────────

class TestPostModel:
    def test_valid_post(self):
        p = Post(slug="hello-world", title="Hello World")
        assert p.slug == "hello-world"
        assert p.title == "Hello World"

    def test_slug_rejects_uppercase(self):
        with pytest.raises(ValidationError):
            Post(slug="Hello-World", title="T")

    def test_slug_rejects_leading_hyphen(self):
        with pytest.raises(ValidationError):
            Post(slug="-bad", title="T")

    def test_slug_rejects_spaces(self):
        with pytest.raises(ValidationError):
            Post(slug="hello world", title="T")

    def test_slug_accepts_digits(self):
        p = Post(slug="post-123", title="T")
        assert p.slug == "post-123"

    def test_blocks_defaults_to_empty_list(self):
        p = Post(slug="s", title="T")
        assert p.blocks == []

    def test_blocks_parsed_from_json_string(self):
        p = Post(slug="s", title="T", blocks='[{"text": "hello"}]')
        assert p.blocks == [{"text": "hello"}]

    def test_blocks_coerces_none_to_empty_list(self):
        p = Post(slug="s", title="T", blocks=None)
        assert p.blocks == []

    def test_blocks_invalid_json_defaults_to_empty_list(self):
        p = Post(slug="s", title="T", blocks="not-json")
        assert p.blocks == []

    def test_published_defaults_to_false(self):
        p = Post(slug="s", title="T")
        assert p.published is False

    def test_og_type_defaults_to_article(self):
        p = Post(slug="s", title="T")
        assert p.og_type == OGType.article

    def test_theme_mode_defaults_to_dark(self):
        p = Post(slug="s", title="T")
        assert p.theme_mode == ThemeMode.dark

    def test_theme_style_defaults_to_professional(self):
        p = Post(slug="s", title="T")
        assert p.theme_style == ThemeStyle.professional

    def test_no_index_defaults_to_false(self):
        p = Post(slug="s", title="T")
        assert p.no_index is False


# ── Page ──────────────────────────────────────────────────────────────────────

class TestPageModel:
    def test_valid_page(self):
        p = Page(slug="about", title="About")
        assert p.slug == "about"

    def test_slug_rejects_invalid(self):
        with pytest.raises(ValidationError):
            Page(slug="About Me", title="T")

    def test_blocks_coerces_none(self):
        p = Page(slug="s", title="T", blocks=None)
        assert p.blocks == []

    def test_published_defaults_to_false(self):
        p = Page(slug="s", title="T")
        assert p.published is False

    def test_page_has_no_og_type(self):
        """og_type removed from Page — always website, not stored."""
        p = Page(slug="s", title="T")
        assert not hasattr(p, 'og_type')


# ── Category ──────────────────────────────────────────────────────────────────

class TestCategoryModel:
    def test_valid_category(self):
        c = Category(slug="design", name="Design")
        assert c.slug == "design"
        assert c.name == "Design"

    def test_slug_rejects_uppercase(self):
        with pytest.raises(ValidationError):
            Category(slug="Design", name="Design")

    def test_max_items_defaults_to_ten(self):
        c = Category(slug="s", name="N")
        assert c.max_items == 10


# ── BrandSettings ─────────────────────────────────────────────────────────────

class TestBrandSettings:
    def test_empty_brand_is_valid(self):
        b = BrandSettings()
        assert b.logo_url == ""
        assert b.favicon_url == ""

    def test_social_fields_default_to_none(self):
        b = BrandSettings()
        assert b.linkedin is None
        assert b.instagram is None
        assert b.email is None

    def test_display_name_and_role_title(self):
        b = BrandSettings(display_name="James Brannon", role_title="Designer")
        assert b.display_name == "James Brannon"
        assert b.role_title == "Designer"


# ── SeoSettings ───────────────────────────────────────────────────────────────

class TestSeoSettings:
    def test_empty_seo_is_valid(self):
        s = SeoSettings()
        assert s.site_name is None
        assert s.seo_description is None
        assert s.og_image is None
        assert s.og_site_name is None
        assert s.no_index is False

    def test_site_name_can_be_set(self):
        s = SeoSettings(site_name="James Brannon")
        assert s.site_name == "James Brannon"

    def test_no_og_type_on_seo_settings(self):
        """og_type removed from SeoSettings — always website at site level."""
        s = SeoSettings()
        assert not hasattr(s, 'og_type')


# ── ProfileSettings ───────────────────────────────────────────────────────────

class TestProfileSettings:
    def test_empty_profile_is_valid(self):
        p = ProfileSettings()
        assert p.headline is None
        assert p.blog is None
        assert p.strengths is None
        assert p.experience is None

    def test_with_blog_settings(self):
        p = ProfileSettings(blog=BlogSettings(headline="Latest", limit=5))
        assert p.blog.headline == "Latest"
        assert p.blog.limit == 5

    def test_blog_limit_defaults_to_three(self):
        b = BlogSettings()
        assert b.limit == 3


# ── StrengthItem / StrengthsSection ───────────────────────────────────────────

class TestStrengthsModels:
    def test_valid_strength_item(self):
        s = StrengthItem(name="Design")
        assert s.name == "Design"
        assert s.description is None

    def test_strength_item_with_description(self):
        s = StrengthItem(name="Design", description="UI/UX work")
        assert s.description == "UI/UX work"

    def test_strengths_section_defaults(self):
        s = StrengthsSection()
        assert s.headline is None
        assert s.items == []

    def test_strengths_section_with_items(self):
        s = StrengthsSection(
            headline="Skills",
            items=[StrengthItem(name="Design"), StrengthItem(name="Code")],
        )
        assert s.headline == "Skills"
        assert len(s.items) == 2
        assert s.items[0].name == "Design"


# ── ExperienceItem / ExperienceSection ────────────────────────────────────────

class TestExperienceModels:
    def test_valid_experience_item(self):
        e = ExperienceItem(job_title="Designer")
        assert e.job_title == "Designer"
        assert e.company is None
        assert e.dates is None
        assert e.summary is None
        assert e.page_link is None

    def test_experience_item_all_fields(self):
        e = ExperienceItem(
            job_title="Senior Designer",
            company="Acme",
            dates="2020–2024",
            summary="<p>Led design.</p>",
            page_link="about",
        )
        assert e.company == "Acme"
        assert e.dates == "2020–2024"
        assert e.summary == "<p>Led design.</p>"
        assert e.page_link == "about"

    def test_experience_section_defaults(self):
        e = ExperienceSection()
        assert e.headline is None
        assert e.items == []

    def test_experience_section_with_items(self):
        e = ExperienceSection(
            headline="Experience",
            items=[ExperienceItem(job_title="Designer", company="Acme")],
        )
        assert e.headline == "Experience"
        assert len(e.items) == 1
        assert e.items[0].company == "Acme"


# ── BlogPageSettings ───────────────────────────────────────────────────────────

class TestBlogPageSettings:
    def test_empty_is_valid(self):
        b = BlogPageSettings()
        assert b.page_headline is None

    def test_with_headline(self):
        b = BlogPageSettings(page_headline="All Posts")
        assert b.page_headline == "All Posts"


# ── BrandSettings dark mode flags ─────────────────────────────────────────────

class TestBrandSettingsDarkMode:
    def test_logo_dark_mode_defaults_to_false(self):
        b = BrandSettings()
        assert b.logo_dark_mode is False

    def test_favicon_dark_mode_defaults_to_false(self):
        b = BrandSettings()
        assert b.favicon_dark_mode is False

    def test_dark_mode_flags_can_be_set(self):
        b = BrandSettings(logo_dark_mode=True, favicon_dark_mode=True)
        assert b.logo_dark_mode is True
        assert b.favicon_dark_mode is True


# ── Enum values ───────────────────────────────────────────────────────────────

class TestEnums:
    def test_theme_mode_values(self):
        assert ThemeMode.dark.value == "dark"
        assert ThemeMode.light.value == "light"

    def test_theme_style_values(self):
        assert ThemeStyle.professional.value == "professional"
        assert ThemeStyle.thoughts.value == "thoughts"

    def test_og_type_values(self):
        assert OGType.website.value == "website"
        assert OGType.article.value == "article"
        assert OGType.profile.value == "profile"
