import pytest

from isales_common.utils.phone import PhoneError, is_valid, normalize


class TestNormalize:
    def test_chinese_mobile_with_country_code(self):
        assert normalize("+8613800001234") == "+8613800001234"

    def test_chinese_mobile_without_country_code(self):
        assert normalize("13800001234", default_region="CN") == "+8613800001234"

    def test_strips_formatting(self):
        assert normalize("+86 138 0000 1234") == "+8613800001234"

    def test_us_number(self):
        assert normalize("+14155552671") == "+14155552671"

    def test_us_number_default_region(self):
        assert normalize("4155552671", default_region="US") == "+14155552671"

    def test_empty_raises(self):
        with pytest.raises(PhoneError):
            normalize("")

    def test_whitespace_raises(self):
        with pytest.raises(PhoneError):
            normalize("   ")

    def test_unparseable_raises(self):
        with pytest.raises(PhoneError):
            normalize("not-a-number")

    def test_invalid_number_raises(self):
        # too short to be a real CN mobile
        with pytest.raises(PhoneError):
            normalize("123", default_region="CN")


class TestIsValid:
    def test_valid_returns_true(self):
        assert is_valid("+8613800001234") is True

    def test_invalid_returns_false(self):
        assert is_valid("not-a-number") is False

    def test_empty_returns_false(self):
        assert is_valid("") is False
