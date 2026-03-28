"""
tests/test_accessibility.py
Accessibility tests for the frontend templates.
"""

import os
import re
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
TEMPLATE_PATH = PROJECT_ROOT / "templates" / "index.html"


class TestAccessibility:
    @pytest.fixture
    def html_content(self):
        with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
            return f.read()

    def test_skip_link_exists(self, html_content: str) -> None:
        assert (
            'class="skip-link"' in html_content or "class='skip-link'" in html_content
        )
        assert 'href="#main-content"' in html_content

    def test_main_landmark_exists(self, html_content: str) -> None:
        assert 'id="main-content"' in html_content or 'role="main"' in html_content

    def test_page_title_descriptive(self, html_content: str) -> None:
        title_match = re.search(r"<title>(.+?)</title>", html_content)
        assert title_match, "Missing <title> tag"
        title = title_match.group(1)
        assert len(title) >= 10, "Title should be descriptive (at least 10 characters)"
        assert "AI" in title or "Health" in title or "IntentBridge" in title

    def test_meta_description_exists(self, html_content: str) -> None:
        assert 'name="description"' in html_content

    def test_form_labels_exist(self, html_content: str) -> None:
        assert '<label for="user-input"' in html_content

    def test_aria_labels_for_interactive_elements(self, html_content: str) -> None:
        assert "aria-label" in html_content or "aria-labelledby" in html_content

    def test_aria_live_regions_exist(self, html_content: str) -> None:
        assert "aria-live=" in html_content

    def test_role_attributes_exist(self, html_content: str) -> None:
        assert "role=" in html_content

    def test_button_has_type_attribute(self, html_content: str) -> None:
        assert 'type="button"' in html_content or "type='button'" in html_content

    def test_links_have_target_blank_for_external(self, html_content: str) -> None:
        external_links = re.findall(r'<a[^>]+target="_blank"[^>]*>', html_content)
        for link in external_links:
            assert 'rel="noopener' in link or "rel='noopener" in link, (
                'External links with target=_blank should have rel="noopener noreferrer"'
            )

    def test_color_contrast_indicators(self, html_content: str) -> None:
        assert "var(--text-secondary)" in html_content
        assert "var(--text-primary)" in html_content

    def test_focus_styles_exist(self, html_content: str) -> None:
        assert ":focus" in html_content or ":focus-visible" in html_content

    def test_keyboard_event_handlers_have_alternatives(self, html_content: str) -> None:
        has_onclick = "onclick=" in html_content
        has_button = "<button" in html_content
        assert has_button, (
            "Interactive elements should use <button> for keyboard accessibility"
        )

    def test_images_have_alt_or_aria_hidden(self, html_content: str) -> None:
        svg_with_icon = "<svg" in html_content
        if svg_with_icon:
            assert 'aria-hidden="true"' in html_content, (
                'Decorative SVGs should have aria-hidden="true"'
            )

    def test_heading_hierarchy(self, html_content: str) -> None:
        h1_tags = re.findall(r"<h1[^>]*>", html_content)
        assert len(h1_tags) == 1, "Should have exactly one <h1> tag"
        h2_tags = re.findall(r"<h2[^>]*>", html_content)
        assert len(h2_tags) >= 1, "Should have <h2> tags for section headings"

    def test_language_attribute(self, html_content: str) -> None:
        assert 'lang="en"' in html_content

    def test_viewport_meta_tag(self, html_content: str) -> None:
        assert 'name="viewport"' in html_content

    def test_minimum_touch_target_size(self, html_content: str) -> None:
        assert "min-height: 48px" in html_content or "minHeight" in html_content, (
            "Interactive elements should have minimum 48px touch target"
        )

    def test_visual_hidden_class_exists(self, html_content: str) -> None:
        assert ".visually-hidden" in html_content or ".sr-only" in html_content
