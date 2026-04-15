"""Unit tests for Vietnamese number-to-words conversion."""

from __future__ import annotations

from erpnextvn.payroll.utils import _read_three_digits, format_vnd, so_tien_bang_chu


class TestReadThreeDigits:
    def test_zero(self):
        assert _read_three_digits(0) == ""

    def test_simple(self):
        assert _read_three_digits(5) == "năm"
        assert _read_three_digits(15) == "mười lăm"
        assert _read_three_digits(21) == "hai mươi mốt"
        assert _read_three_digits(24) == "hai mươi tư"

    def test_hundreds(self):
        assert _read_three_digits(115) == "một trăm mười lăm"
        assert _read_three_digits(121) == "một trăm hai mươi mốt"
        assert _read_three_digits(105) == "một trăm lẻ năm"
        assert _read_three_digits(100) == "một trăm"

    def test_zero_hundred_prefix(self):
        # Used for non-leading groups.
        assert "không trăm" in _read_three_digits(5, show_zero_hundred=True)


class TestSoTienBangChu:
    def test_zero(self):
        assert so_tien_bang_chu(0) == "Không đồng"

    def test_simple(self):
        assert so_tien_bang_chu(1000) == "Một nghìn đồng"
        assert so_tien_bang_chu(1_000_000) == "Một triệu đồng"
        assert so_tien_bang_chu(1_000_000_000) == "Một tỷ đồng"

    def test_complex(self):
        result = so_tien_bang_chu(1_234_567)
        # Capitalized first letter, ends with "đồng"
        assert result.startswith("Một triệu")
        assert result.endswith("đồng")

    def test_custom_currency(self):
        assert so_tien_bang_chu(100, currency="USD").endswith("USD")

    def test_negative_rendered_as_positive(self):
        # Absolute value is used.
        assert so_tien_bang_chu(-500) == so_tien_bang_chu(500)

    def test_rounds_to_integer(self):
        assert so_tien_bang_chu(1000.4) == so_tien_bang_chu(1000)


class TestFormatVnd:
    def test_basic(self):
        assert format_vnd(1_234_567) == "1.234.567 ₫"

    def test_zero(self):
        assert format_vnd(0) == "0 ₫"

    def test_rounds(self):
        assert format_vnd(1234.7) == "1.235 ₫"
