"""Title Sanitizer — cleans eBay titles for Cassini SEO optimization."""

import re

from flipflow.core.schemas.title import TitleSanitizeRequest, TitleSanitizeResponse

# Junk patterns: repeated special chars, non-alphanumeric noise
_JUNK_CHARS = re.compile(r"[!*~@#$%^&]{2,}")
_SPECIAL_CHARS = re.compile(r"[^\w\s\-&/.,'+()#]")
_MULTI_SPACES = re.compile(r"\s{2,}")

# Words that confuse Cassini and look spammy
_BANNED_WORDS = {
    "l@@k", "look!", "look!!", "wow", "wow!", "must see", "a+++", "a++",
    "nr", "no reserve", "free shipping", "fast shipping", "hot", "sexy",
    "rare!", "amazing", "incredible", "awesome", "perfect", "beautiful",
    "gorgeous", "stunning", "excellent!", "great!", "nice!", "cool!",
}

# Known acronyms that should stay uppercase
_KNOWN_ACRONYMS = {
    "nib", "nwt", "nwb", "nwot", "euc", "vgc", "guc", "oem", "oob",
    "usb", "hdmi", "led", "lcd", "dvd", "cd", "pc", "tv", "ac", "dc",
    "xl", "xxl", "xs", "sm", "md", "lg", "oz", "ml", "gb", "tb", "mb",
    "hp", "ps", "hd", "sd", "rgb", "ddr", "ssd", "hdd", "rpm", "mph",
    "nfl", "nba", "mlb", "nhl", "usa", "uk", "eu",
}

MAX_TITLE_LENGTH = 80


class TitleSanitizer:
    """Cleans and optimizes eBay listing titles.

    Rules:
    1. Strip junk characters and repeated special chars
    2. Remove banned spam words
    3. Normalize ALL CAPS → Title Case (preserve known acronyms)
    4. Front-load Brand + Model in first 30 characters
    5. Enforce 80-character limit
    """

    def sanitize(self, request: TitleSanitizeRequest) -> TitleSanitizeResponse:
        """Run full sanitization pipeline on a title."""
        original = request.title
        changes: list[str] = []
        title = original

        # Step 1: Strip junk
        cleaned = self._strip_junk(title)
        if cleaned != title:
            changes.append("Removed junk characters")
        title = cleaned

        # Step 2: Remove banned words
        cleaned = self._remove_banned_words(title)
        if cleaned != title:
            changes.append("Removed spam words")
        title = cleaned

        # Step 3: Normalize case
        cleaned = self._normalize_case(title)
        if cleaned != title:
            changes.append("Normalized casing")
        title = cleaned

        # Step 4: Front-load brand/model
        if request.brand or request.model:
            cleaned = self._front_load_brand_model(
                title, request.brand, request.model,
            )
            if cleaned != title:
                changes.append("Moved brand/model to front")
            title = cleaned

        # Step 5: Enforce length
        cleaned = self._enforce_length(title)
        if cleaned != title:
            changes.append(f"Trimmed to {MAX_TITLE_LENGTH} chars")
        title = cleaned

        # Final cleanup: collapse spaces
        title = _MULTI_SPACES.sub(" ", title).strip()

        brand_model_front = self._check_brand_model_front(
            title, request.brand, request.model,
        )

        if not changes:
            changes.append("No changes needed")

        return TitleSanitizeResponse(
            original=original,
            sanitized=title,
            changes=changes,
            length=len(title),
            brand_model_in_front=brand_model_front,
        )

    def _strip_junk(self, title: str) -> str:
        """Remove repeated special characters and non-standard symbols."""
        title = _JUNK_CHARS.sub("", title)
        title = _SPECIAL_CHARS.sub("", title)
        return _MULTI_SPACES.sub(" ", title).strip()

    def _remove_banned_words(self, title: str) -> str:
        """Remove known spam words (case-insensitive)."""
        words = title.split()
        result = []
        i = 0
        while i < len(words):
            # Check two-word phrases
            if i + 1 < len(words):
                pair = f"{words[i]} {words[i+1]}".lower()
                if pair in _BANNED_WORDS:
                    i += 2
                    continue
            # Check single words
            if words[i].lower().rstrip("!") in _BANNED_WORDS or words[i].lower() in _BANNED_WORDS:
                i += 1
                continue
            result.append(words[i])
            i += 1
        return " ".join(result)

    def _normalize_case(self, title: str) -> str:
        """Convert ALL CAPS words to Title Case, preserving known acronyms."""
        words = title.split()
        result = []
        for word in words:
            clean = word.strip(".,!-()#")
            if clean.upper() == clean and len(clean) > 1 and clean.isalpha():
                # It's ALL CAPS
                if clean.lower() in _KNOWN_ACRONYMS:
                    result.append(word.upper())
                else:
                    result.append(word.capitalize())
            else:
                result.append(word)
        return " ".join(result)

    def _front_load_brand_model(
        self, title: str, brand: str | None, model: str | None,
    ) -> str:
        """Move brand and model to the beginning of the title."""
        prefix_parts: list[str] = []
        remaining = title

        if brand:
            # Remove existing brand mention (case-insensitive)
            pattern = re.compile(re.escape(brand), re.IGNORECASE)
            remaining = pattern.sub("", remaining).strip()
            prefix_parts.append(brand)

        if model:
            pattern = re.compile(re.escape(model), re.IGNORECASE)
            remaining = pattern.sub("", remaining).strip()
            prefix_parts.append(model)

        remaining = _MULTI_SPACES.sub(" ", remaining).strip()
        # Remove leading separators after extraction
        remaining = remaining.lstrip("-–— ")

        if prefix_parts:
            prefix = " ".join(prefix_parts)
            return f"{prefix} {remaining}" if remaining else prefix

        return remaining

    def _enforce_length(self, title: str) -> str:
        """Trim title to 80 characters, breaking at word boundaries."""
        if len(title) <= MAX_TITLE_LENGTH:
            return title

        truncated = title[:MAX_TITLE_LENGTH]
        # Break at last space to avoid cutting words
        last_space = truncated.rfind(" ")
        if last_space > MAX_TITLE_LENGTH // 2:
            return truncated[:last_space].rstrip()
        return truncated.rstrip()

    def _check_brand_model_front(
        self, title: str, brand: str | None, model: str | None,
    ) -> bool:
        """Check if brand/model appears in the first 30 characters."""
        front = title[:30].lower()
        if brand and brand.lower() not in front:
            return False
        if model and model.lower() not in front:
            return False
        return True
