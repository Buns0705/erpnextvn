"""Unit tests for the Vietnamese Personal Income Tax calculator."""

from __future__ import annotations

from erpnextvn.payroll.pit_calculator import TAX_BRACKETS, calculate_pit


class TestCalculatePit:
    # Using explicit deductions to avoid the ``VN Payroll Settings`` lookup.
    PERSONAL = 11_000_000.0
    DEPENDENT = 4_400_000.0

    def _pit(self, gross: float, insurance: float = 0, deps: int = 0) -> float:
        return calculate_pit(
            gross,
            insurance,
            num_dependents=deps,
            personal_deduction=self.PERSONAL,
            dependent_deduction=self.DEPENDENT,
        ).tax_amount

    def test_below_threshold(self):
        # Gross 10M, no insurance, no dependents → taxable = −1M → 0
        r = calculate_pit(10_000_000, 0, 0, self.PERSONAL, self.DEPENDENT)
        assert r.tax_amount == 0
        assert r.bracket == 0
        assert r.taxable_income == 0

    def test_bracket_1(self):
        # Taxable 4M → 4M * 5% − 0 = 200k
        r = calculate_pit(15_000_000, 0, 0, self.PERSONAL, self.DEPENDENT)
        assert r.taxable_income == 4_000_000
        assert r.tax_amount == 200_000
        assert r.bracket == 1

    def test_bracket_3(self):
        # Taxable 15M → 15M * 15% − 750k = 1.5M
        r = calculate_pit(26_000_000, 0, 0, self.PERSONAL, self.DEPENDENT)
        assert r.taxable_income == 15_000_000
        assert r.tax_amount == 1_500_000
        assert r.bracket == 3

    def test_bracket_7(self):
        # Taxable 100M → 100M * 35% − 9.85M = 25.15M
        r = calculate_pit(111_000_000, 0, 0, self.PERSONAL, self.DEPENDENT)
        assert r.taxable_income == 100_000_000
        assert r.tax_amount == 25_150_000
        assert r.bracket == 7

    def test_dependents_reduce_tax(self):
        without = self._pit(30_000_000, 0, 0)
        with_two = self._pit(30_000_000, 0, 2)
        assert with_two < without

    def test_insurance_reduces_tax(self):
        no_bh = self._pit(30_000_000, 0, 0)
        with_bh = self._pit(30_000_000, 2_000_000, 0)
        assert with_bh < no_bh

    def test_effective_rate_bounded(self):
        r = calculate_pit(20_000_000, 0, 0, self.PERSONAL, self.DEPENDENT)
        assert 0 <= r.effective_rate < 35.0

    def test_bracket_table_monotonic(self):
        # Upper limits must strictly increase; rates must strictly increase.
        limits = [b[0] for b in TAX_BRACKETS]
        rates = [b[1] for b in TAX_BRACKETS]
        assert limits == sorted(limits)
        assert rates == sorted(rates)

    def test_statutory_defaults_per_nq110(self):
        """Defaults should follow Resolution 110/2025/UBTVQH15 when Frappe is unavailable."""
        from erpnextvn.payroll.pit_calculator import _resolve_deductions

        personal, dependent = _resolve_deductions(None, None)
        assert personal == 15_500_000.0
        assert dependent == 6_200_000.0

    def test_nq110_lifts_zero_threshold(self):
        # Under NQ 110 defaults, gross 15M with 0 deps yields no tax
        # (taxable = 15M − 15.5M = negative → 0).
        r = calculate_pit(15_000_000, 0, 0)  # No overrides, uses defaults
        assert r.tax_amount == 0
        assert r.taxable_income == 0
