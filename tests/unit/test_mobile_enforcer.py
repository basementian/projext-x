"""Tests for Mobile Enforcer — HTML stripping and responsive template."""

import pytest

from flipflow.core.services.gatekeeper.mobile_enforcer import MobileEnforcer


@pytest.fixture
def enforcer():
    return MobileEnforcer()


class TestHTMLStripping:
    def test_strips_basic_html_tags(self, enforcer):
        html = "<p>Hello <b>World</b></p>"
        result = enforcer.strip_html(html)
        assert "<p>" not in result
        assert "<b>" not in result
        assert "Hello" in result
        assert "World" in result

    def test_strips_style_blocks(self, enforcer):
        html = "<style>.foo { color: red; }</style><p>Content</p>"
        result = enforcer.strip_html(html)
        assert "color" not in result
        assert ".foo" not in result
        assert "Content" in result

    def test_strips_script_blocks(self, enforcer):
        html = "<script>alert('xss')</script><p>Safe content</p>"
        result = enforcer.strip_html(html)
        assert "alert" not in result
        assert "script" not in result
        assert "Safe content" in result

    def test_strips_html_comments(self, enforcer):
        html = "<!-- hidden comment --><p>Visible</p>"
        result = enforcer.strip_html(html)
        assert "hidden" not in result
        assert "Visible" in result

    def test_decodes_html_entities(self, enforcer):
        html = "Salt &amp; Pepper &lt;3"
        result = enforcer.strip_html(html)
        assert "Salt & Pepper" in result

    def test_handles_nbsp(self, enforcer):
        html = "Word&nbsp;Another"
        result = enforcer.strip_html(html)
        assert "Word Another" in result

    def test_collapses_whitespace(self, enforcer):
        html = "Word     with    spaces"
        result = enforcer.strip_html(html)
        assert "     " not in result

    def test_empty_input(self, enforcer):
        assert enforcer.strip_html("") == ""

    def test_plain_text_unchanged(self, enforcer):
        text = "Just a plain text description"
        result = enforcer.strip_html(text)
        assert result == text

    def test_complex_ebay_html(self, enforcer):
        html = """
        <div style="width:1200px;margin:0 auto;">
            <style>
                .header { font-size: 10px; }
                table { width: 100%; }
            </style>
            <table>
                <tr><td>Brand</td><td>Nike</td></tr>
                <tr><td>Size</td><td>10</td></tr>
            </table>
            <p style="font-size:8px;">Tiny disclaimer text</p>
            <div class="description">
                <h2>Nike Air Max 90</h2>
                <p>Great condition, barely worn.</p>
                <p>Ships within 1 business day.</p>
            </div>
        </div>
        """
        result = enforcer.strip_html(html)
        assert "Nike" in result
        assert "Size" in result
        assert "10" in result
        assert "Great condition" in result
        assert "<style>" not in result
        assert "<table>" not in result
        assert "font-size" not in result


class TestTemplate:
    def test_wraps_in_responsive_div(self, enforcer):
        result = enforcer.wrap_in_template("Hello World")
        assert "max-width:800px" in result
        assert "font-size:16px" in result
        assert "Hello World" in result

    def test_converts_paragraphs(self, enforcer):
        result = enforcer.wrap_in_template("Para 1\n\nPara 2")
        assert "<p" in result
        assert "Para 1" in result
        assert "Para 2" in result

    def test_enforce_returns_template(self, enforcer):
        html = "<b>Bold text</b>"
        result = enforcer.enforce(html)
        assert "max-width:800px" in result
        assert "Bold text" in result
        assert "<b>" not in result

    def test_enforce_empty_returns_empty(self, enforcer):
        result = enforcer.enforce("")
        assert result == ""

    def test_enforce_whitespace_only_returns_empty(self, enforcer):
        result = enforcer.enforce("   <br>   <p></p>  ")
        assert result == ""


class TestMobileSafetyCheck:
    def test_simple_html_is_safe(self, enforcer):
        html = '<p style="font-size:16px;">Hello</p>'
        assert enforcer.is_mobile_safe(html) is True

    def test_fixed_width_not_safe(self, enforcer):
        html = '<div style="width:1200px;">Content</div>'
        assert enforcer.is_mobile_safe(html) is False

    def test_small_font_not_safe(self, enforcer):
        html = '<p style="font-size:8px;">Tiny text</p>'
        assert enforcer.is_mobile_safe(html) is False

    def test_table_not_safe(self, enforcer):
        html = "<table><tr><td>Data</td></tr></table>"
        assert enforcer.is_mobile_safe(html) is False

    def test_style_block_not_safe(self, enforcer):
        html = "<style>.foo { color: red; }</style><p>Content</p>"
        assert enforcer.is_mobile_safe(html) is False

    def test_plain_text_is_safe(self, enforcer):
        assert enforcer.is_mobile_safe("Just plain text") is True
