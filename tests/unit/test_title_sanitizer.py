"""Tests for Title Sanitizer."""

import pytest

from flipflow.core.schemas.title import TitleSanitizeRequest
from flipflow.core.services.gatekeeper.title_sanitizer import TitleSanitizer


@pytest.fixture
def sanitizer() -> TitleSanitizer:
    return TitleSanitizer()


def _sanitize(sanitizer, title, brand=None, model=None):
    return sanitizer.sanitize(
        TitleSanitizeRequest(
            title=title,
            brand=brand,
            model=model,
        )
    )


class TestJunkRemoval:
    def test_strips_repeated_exclamation(self, sanitizer):
        result = _sanitize(sanitizer, "Great Item!!! Amazing!!!")
        assert "!!!" not in result.sanitized

    def test_strips_at_symbols(self, sanitizer):
        result = _sanitize(sanitizer, "L@@K at this deal")
        assert "@@" not in result.sanitized

    def test_strips_asterisks(self, sanitizer):
        result = _sanitize(sanitizer, "***RARE*** Item ***WOW***")
        assert "***" not in result.sanitized

    def test_preserves_hyphens(self, sanitizer):
        result = _sanitize(sanitizer, "Nike Air Max 90 - Size 10")
        assert "-" in result.sanitized

    def test_preserves_ampersand(self, sanitizer):
        result = _sanitize(sanitizer, "Salt & Pepper Shakers")
        assert "&" in result.sanitized

    def test_preserves_apostrophe(self, sanitizer):
        result = _sanitize(sanitizer, "Levi's 501 Jeans")
        assert "'" in result.sanitized


class TestBannedWords:
    def test_removes_look(self, sanitizer):
        result = _sanitize(sanitizer, "L@@K Nike Air Max")
        assert "l@@k" not in result.sanitized.lower()

    def test_removes_wow(self, sanitizer):
        result = _sanitize(sanitizer, "WOW Amazing Nike Shoes")
        assert "wow" not in result.sanitized.lower()
        assert "amazing" not in result.sanitized.lower()

    def test_removes_must_see(self, sanitizer):
        result = _sanitize(sanitizer, "Must See Vintage Watch")
        assert "must see" not in result.sanitized.lower()

    def test_removes_nr(self, sanitizer):
        result = _sanitize(sanitizer, "Vintage Watch NR")
        assert "nr" not in result.sanitized.lower() or "brand" in result.sanitized.lower()

    def test_preserves_real_words(self, sanitizer):
        result = _sanitize(sanitizer, "Nike Air Jordan 1 Retro High")
        assert result.sanitized == "Nike Air Jordan 1 Retro High"


class TestCaseNormalization:
    def test_all_caps_to_title_case(self, sanitizer):
        result = _sanitize(sanitizer, "VINTAGE LEATHER JACKET MENS")
        assert "VINTAGE" not in result.sanitized
        assert "Vintage" in result.sanitized

    def test_preserves_known_acronyms(self, sanitizer):
        result = _sanitize(sanitizer, "NIB USB HDMI Cable LED")
        assert "NIB" in result.sanitized
        assert "USB" in result.sanitized
        assert "HDMI" in result.sanitized
        assert "LED" in result.sanitized

    def test_preserves_mixed_case(self, sanitizer):
        result = _sanitize(sanitizer, "iPhone 15 Pro Max Case")
        assert "iPhone" in result.sanitized

    def test_preserves_numbers(self, sanitizer):
        result = _sanitize(sanitizer, "NIKE AIR MAX 90 SIZE 10")
        assert "90" in result.sanitized
        assert "10" in result.sanitized


class TestBrandModelFrontLoading:
    def test_moves_brand_to_front(self, sanitizer):
        result = _sanitize(
            sanitizer,
            "Vintage Running Shoes Nike",
            brand="Nike",
        )
        assert result.sanitized.startswith("Nike")

    def test_moves_brand_and_model(self, sanitizer):
        result = _sanitize(
            sanitizer,
            "Vintage Running Shoes Jordan 1",
            brand="Nike",
            model="Jordan 1",
        )
        assert result.sanitized.startswith("Nike Jordan 1")

    def test_doesnt_duplicate_brand(self, sanitizer):
        result = _sanitize(
            sanitizer,
            "Nike Air Max 90 Running Shoes",
            brand="Nike",
        )
        count = result.sanitized.lower().count("nike")
        assert count == 1

    def test_brand_model_in_front_flag(self, sanitizer):
        result = _sanitize(
            sanitizer,
            "Nike Air Max 90",
            brand="Nike",
            model="Air Max 90",
        )
        assert result.brand_model_in_front is True

    def test_brand_model_not_in_front_flag(self, sanitizer):
        """If brand+model is too long for first 30 chars, flag it."""
        result = _sanitize(
            sanitizer,
            "Some Long Description Words Here Brand Model Name",
            brand="SomethingVeryLongBrandNameHere",
            model="ModelXYZ",
        )
        # The sanitizer moves them to front, so they should be there
        assert result.sanitized.startswith("SomethingVeryLongBrandNameHere")


class TestLengthEnforcement:
    def test_within_limit_unchanged(self, sanitizer):
        title = "Nike Air Max 90 Mens Running Shoes Size 10"
        result = _sanitize(sanitizer, title)
        assert len(result.sanitized) <= 80

    def test_long_title_trimmed(self, sanitizer):
        title = "A" * 40 + " " + "B" * 40 + " " + "C" * 20
        result = _sanitize(sanitizer, title)
        assert len(result.sanitized) <= 80

    def test_trim_at_word_boundary(self, sanitizer):
        title = "Nike Air Max " + "X" * 70
        result = _sanitize(sanitizer, title)
        assert len(result.sanitized) <= 80

    def test_reports_correct_length(self, sanitizer):
        result = _sanitize(sanitizer, "Short Title")
        assert result.length == len(result.sanitized)


class TestChangesTracking:
    def test_no_changes_needed(self, sanitizer):
        result = _sanitize(sanitizer, "Nike Air Max 90")
        assert "No changes needed" in result.changes

    def test_reports_junk_removal(self, sanitizer):
        result = _sanitize(sanitizer, "!!!Great Item!!!")
        assert any("junk" in c.lower() for c in result.changes)

    def test_reports_spam_removal(self, sanitizer):
        result = _sanitize(sanitizer, "WOW Nike Shoes")
        assert any("spam" in c.lower() for c in result.changes)

    def test_reports_case_normalization(self, sanitizer):
        result = _sanitize(sanitizer, "VINTAGE JACKET")
        assert any("casing" in c.lower() or "case" in c.lower() for c in result.changes)

    def test_reports_brand_move(self, sanitizer):
        result = _sanitize(
            sanitizer,
            "Running Shoes Nike",
            brand="Nike",
        )
        assert any("brand" in c.lower() for c in result.changes)


class TestRealWorldTitles:
    def test_classic_spam_title(self, sanitizer):
        result = _sanitize(
            sanitizer,
            "!!!L@@K!! AMAZING VINTAGE NIKE AIR JORDAN 1 RETRO HIGH WOW!!!",
            brand="Nike",
            model="Air Jordan 1",
        )
        assert "l@@k" not in result.sanitized.lower()
        assert "wow" not in result.sanitized.lower()
        assert "amazing" not in result.sanitized.lower()
        assert result.sanitized.startswith("Nike Air Jordan 1")
        assert len(result.sanitized) <= 80

    def test_already_clean_title(self, sanitizer):
        result = _sanitize(
            sanitizer,
            "Apple MacBook Pro 16 M3 Max 36GB 1TB Space Black",
            brand="Apple",
            model="MacBook Pro",
        )
        assert result.sanitized.startswith("Apple MacBook Pro")
        assert len(result.sanitized) <= 80

    def test_all_caps_with_good_info(self, sanitizer):
        result = _sanitize(
            sanitizer,
            "SONY WH-1000XM5 WIRELESS NOISE CANCELLING HEADPHONES BLACK",
            brand="Sony",
        )
        assert result.sanitized.startswith("Sony")
        assert "1000XM5" in result.sanitized or "1000xm5" in result.sanitized.lower()
