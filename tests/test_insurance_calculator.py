"""Unit tests for the Vietnamese social-insurance calculator."""

from __future__ import annotations

from erpnextvn.payroll.insurance_calculator import _DEFAULTS, calculate_insurance


class TestCalculateInsurance:
    def test_below_ceiling_region_1(self):
        # Salary 10M, region I — below both ceilings.
        r = calculate_insurance(10_000_000, "I")
        assert r.si_employee == round(10_000_000 * 0.08)
        assert r.hi_employee == round(10_000_000 * 0.015)
        assert r.ui_employee == round(10_000_000 * 0.01)
        assert r.total_employee == r.si_employee + r.hi_employee + r.ui_employee

    def test_si_hi_ceiling_applied(self):
        # Salary well above 20 × base_salary (= 46.8M).
        r = calculate_insurance(100_000_000, "I")
        ceiling = 20 * _DEFAULTS["base_salary"]
        assert r.si_employee == round(ceiling * 0.08)
        assert r.hi_employee == round(ceiling * 0.015)

    def test_ui_ceiling_region_specific(self):
        # UI ceiling depends on regional minimum wage.
        r1 = calculate_insurance(200_000_000, "I")
        r4 = calculate_insurance(200_000_000, "IV")
        # Region I min wage > Region IV, so UI employer > in region I.
        assert r1.ui_employer > r4.ui_employer

    def test_employer_includes_union_fee(self):
        r = calculate_insurance(10_000_000, "I")
        assert r.union_fee == round(10_000_000 * 0.02)
        assert r.total_employer == (
            r.si_employer + r.hi_employer + r.ui_employer + r.union_fee
        )

    def test_union_fee_uses_total_payroll_when_provided(self):
        r = calculate_insurance(10_000_000, "I", total_payroll=50_000_000)
        assert r.union_fee == round(50_000_000 * 0.02)
