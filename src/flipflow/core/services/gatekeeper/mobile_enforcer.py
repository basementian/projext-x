"""Mobile Enforcer — strips bloated HTML and injects responsive templates.

Research: 80% of eBay traffic is mobile. Listings with horizontal scrolling,
tiny text, or complex CSS are penalized in Mobile Search.

This service strips all HTML/CSS from descriptions and injects them into
a clean, responsive template with 16px font minimum.
"""

import re

# Patterns to strip
_HTML_TAG = re.compile(r"<[^>]+>")
_CSS_BLOCK = re.compile(r"<style[^>]*>.*?</style>", re.DOTALL | re.IGNORECASE)
_SCRIPT_BLOCK = re.compile(r"<script[^>]*>.*?</script>", re.DOTALL | re.IGNORECASE)
_HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
_HTML_ENTITY = re.compile(r"&[a-zA-Z]+;|&#\d+;")
_MULTI_NEWLINES = re.compile(r"\n{3,}")
_MULTI_SPACES = re.compile(r"[ \t]{2,}")

# Responsive template
_MOBILE_TEMPLATE = """<div style="max-width:800px;margin:0 auto;padding:16px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;font-size:16px;line-height:1.6;color:#333;">
{content}
</div>"""

# Common HTML entities to readable text
_ENTITY_MAP = {
    "&amp;": "&",
    "&lt;": "<",
    "&gt;": ">",
    "&quot;": '"',
    "&apos;": "'",
    "&nbsp;": " ",
    "&#39;": "'",
    "&#34;": '"',
}


class MobileEnforcer:
    """Strips HTML/CSS from descriptions and wraps in a responsive template.

    Rules:
    1. Remove all <script> and <style> blocks entirely
    2. Remove HTML comments
    3. Strip all remaining HTML tags
    4. Decode HTML entities to plain text
    5. Clean up excessive whitespace
    6. Wrap in a responsive template with 16px min font
    """

    def enforce(self, html_description: str) -> str:
        """Convert an HTML description to mobile-friendly format.

        Returns the cleaned description wrapped in a responsive template.
        """
        text = self.strip_html(html_description)
        if not text.strip():
            return ""
        return self.wrap_in_template(text)

    def strip_html(self, html: str) -> str:
        """Strip all HTML, CSS, and scripts, returning plain text."""
        text = html

        # Remove script and style blocks first (before stripping tags)
        text = _SCRIPT_BLOCK.sub("", text)
        text = _CSS_BLOCK.sub("", text)
        text = _HTML_COMMENT.sub("", text)

        # Strip remaining HTML tags
        text = _HTML_TAG.sub("\n", text)

        # Decode HTML entities
        for entity, char in _ENTITY_MAP.items():
            text = text.replace(entity, char)
        # Remove any remaining entities
        text = _HTML_ENTITY.sub("", text)

        # Clean up whitespace
        text = _MULTI_SPACES.sub(" ", text)
        text = _MULTI_NEWLINES.sub("\n\n", text)

        # Strip each line and remove empty lines
        lines = [line.strip() for line in text.split("\n")]
        lines = [line for line in lines if line]

        return "\n".join(lines)

    def wrap_in_template(self, plain_text: str) -> str:
        """Wrap plain text in the responsive mobile template."""
        # Convert newlines to <br> for HTML rendering
        paragraphs = plain_text.split("\n\n")
        html_parts = []
        for para in paragraphs:
            clean = para.replace("\n", "<br>")
            html_parts.append(f'<p style="margin:0 0 12px 0;">{clean}</p>')
        content = "\n".join(html_parts)
        return _MOBILE_TEMPLATE.format(content=content)

    def is_mobile_safe(self, html: str) -> bool:
        """Check if a description is already mobile-safe.

        Returns False if it contains:
        - <div> tags with explicit widths
        - Fixed-width tables
        - Small font sizes
        - Complex CSS
        """
        lower = html.lower()

        # Check for problematic patterns
        has_fixed_width = bool(re.search(r"width\s*:\s*\d{4,}px", lower))
        has_small_font = bool(re.search(r"font-size\s*:\s*(\d+)(px|pt)", lower))
        has_tables = "<table" in lower
        has_complex_css = "<style" in lower

        if has_small_font:
            match = re.search(r"font-size\s*:\s*(\d+)(px|pt)", lower)
            if match:
                size = int(match.group(1))
                unit = match.group(2)
                if unit == "px" and size < 14:
                    return False
                if unit == "pt" and size < 11:
                    return False

        return not (has_fixed_width or has_tables or has_complex_css)
