# ERPNext Vietnam — erpnextvn

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![ERPNext v16](https://img.shields.io/badge/ERPNext-v16-green.svg)](https://erpnext.com)
[![Frappe v16](https://img.shields.io/badge/Frappe-v16-green.svg)](https://frappeframework.com)

**Vietnamese Localization for ERPNext v16** — Kế toán, thuế, hóa đơn điện tử, lương, dịch thuật theo chuẩn Việt Nam.

---

## 🇬🇧 English

`erpnextvn` is a comprehensive Vietnamese localization pack for ERPNext v16 / Frappe v16. It ships:

- **Chart of Accounts** — TT200/2014/TT-BTC (full) and TT133/2016/TT-BTC (SME)
- **VAT templates** — 0% / 5% / 8% / 10% Sales & Purchase
- **Payroll** — Personal Income Tax (7-bracket progressive), BHXH / BHYT / BHTN
- **E-Invoicing** — Viettel S-Invoice, VNPT, MISA meInvoice, FPT, BKAV
- **Print Formats** — 8 standard Vietnamese forms (Hóa đơn, Phiếu thu/chi/xuất/nhập, Báo giá, PO, Phiếu lương)
- **Reports** — Bảng lương tháng, Báo cáo TNCN, Bảng kê hóa đơn, Sổ cái, Cân đối phát sinh
- **Translation** — 500+ Vietnamese terms
- **63 provinces** fixture with wage region mapping (I–IV)

## 🇻🇳 Tiếng Việt

`erpnextvn` là bộ bản địa hóa đầy đủ cho ERPNext v16 / Frappe v16 theo chuẩn Việt Nam:

- **Hệ thống tài khoản** — Đầy đủ theo Thông tư 200 và 133
- **Mẫu thuế GTGT** — 0% / 5% / 8% / 10% cho hóa đơn bán/mua
- **Tiền lương** — Thuế TNCN bậc thang 7 bậc, BHXH / BHYT / BHTN
- **Hóa đơn điện tử** — Tích hợp 5 nhà cung cấp lớn (Viettel, VNPT, MISA, FPT, BKAV)
- **Mẫu in** — 8 mẫu chuẩn Việt Nam
- **Báo cáo** — 5 báo cáo theo chuẩn kế toán VN
- **Dịch tiếng Việt** — 500+ thuật ngữ
- **63 tỉnh/thành** — Kèm vùng lương tối thiểu (I–IV)

---

## 📦 Installation

```bash
# On your Frappe bench
cd frappe-bench
bench get-app https://github.com/mrhuychien/erpnextvn
bench --site [your-site] install-app erpnextvn
bench --site [your-site] migrate
```

After installation:

1. Open ERPNext → **Setup Wizard** → select country **Vietnam**
2. Go to **VN Payroll Settings** and verify statutory values
3. Go to **VN E Invoice Settings** and configure your HĐĐT provider (if used)
4. Open **VN Province** to confirm 63 provinces loaded

## ⚙️ Configuration

### Payroll (Lương & Thuế TNCN)

1. Go to `VN Payroll Settings` (Single DocType).
2. Verify statutory defaults:
   - Lương cơ sở: 2,340,000 VND
   - Giảm trừ bản thân: 11,000,000 VND
   - Giảm trừ người phụ thuộc: 4,400,000 VND
   - Tỷ lệ BHXH / BHYT / BHTN (NLĐ 8% / 1.5% / 1%, DN 17.5% / 3% / 1%)
   - Vùng lương: Vùng I 4,960,000 / Vùng II 4,410,000 / ...
3. Khi tạo Salary Slip, các trường VN (BHXH, Thuế TNCN, Thu nhập tính thuế) sẽ được tự động tính.

### Hóa đơn điện tử

1. Go to `VN E Invoice Settings`.
2. Chọn nhà cung cấp (Viettel / VNPT / MISA / FPT / BKAV).
3. Nhập thông tin đăng nhập và chứng thư số.
4. Bật **Sandbox mode** để test trước.
5. Khi submit Sales Invoice, hoặc click nút **"Phát hành HĐĐT"**.

## 🧪 Testing

```bash
# Unit tests (no Frappe bench needed for pure-Python utilities)
cd /path/to/erpnextvn
python -m pytest erpnextvn/payroll/ -v

# Frappe-integrated tests
bench --site [site] run-tests --app erpnextvn
```

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## 📄 License

GPL v3 — see [LICENSE](LICENSE).

## 👥 Credits

- **Publisher:** 1nguoi.com
- **Email:** hello@1nguoi.com
- **Repository:** https://github.com/mrhuychien/erpnextvn
