# Đóng góp cho erpnextvn

Cảm ơn bạn quan tâm đến dự án! Bản địa hóa Việt Nam cho ERPNext là nỗ lực của cộng đồng — mọi đóng góp đều được trân trọng.

## 🚀 Bắt đầu

### 1. Fork & Clone

```bash
git clone https://github.com/YOUR_USERNAME/erpnextvn.git
cd erpnextvn
```

### 2. Thêm repo gốc làm upstream

```bash
git remote add upstream https://github.com/mrhuychien/erpnextvn.git
```

### 3. Tạo branch mới

```bash
git checkout -b feature/ten-tinh-nang
# hoặc
git checkout -b fix/mo-ta-bug
```

## 📝 Code style

- **Python:** PEP 8, sử dụng `ruff` để lint/format
- **JavaScript:** Chuẩn ES2020+
- **Docstrings:** Tất cả bằng tiếng Anh
- **Type hints:** Bắt buộc cho hàm public
- **User-facing strings:** Bằng tiếng Việt (thông qua `_()` hoặc `__()`)
- **Variable/Function names:** Bằng tiếng Anh

### Ví dụ:

```python
def calculate_pit(gross_income: float, num_dependents: int = 0) -> float:
    """Calculate Vietnamese Personal Income Tax.
    
    Args:
        gross_income: Total gross salary.
        num_dependents: Number of registered dependents.
    
    Returns:
        PIT amount in VND.
    """
    # Error messages in Vietnamese
    if gross_income < 0:
        frappe.throw(_("Thu nhập không được âm"))
    ...
```

## 🧪 Chạy tests

```bash
# Unit tests (không cần Frappe bench)
python -m pytest erpnextvn/payroll/ -v

# Frappe-integrated tests
bench --site [test-site] run-tests --app erpnextvn
```

## 📬 Pull Request

1. Đảm bảo tests pass
2. Commit với message rõ ràng:
   - `feat: thêm báo cáo XXX`
   - `fix: sửa lỗi tính thuế TNCN`
   - `docs: cập nhật README`
   - `refactor: tái cấu trúc module Y`
3. Push lên fork của bạn:
   ```bash
   git push origin feature/ten-tinh-nang
   ```
4. Mở Pull Request trên GitHub, mô tả rõ:
   - Vấn đề đang giải quyết
   - Cách tiếp cận
   - Cách test
   - Screenshot (nếu là UI)

## 🐛 Báo lỗi

Mở issue trên GitHub với:

- Mô tả lỗi
- Các bước tái hiện
- Kết quả mong đợi vs kết quả thực tế
- Version ERPNext/Frappe/erpnextvn
- Log/traceback (nếu có)

## 💬 Thảo luận

- GitHub Discussions cho câu hỏi chung
- GitHub Issues cho bug/feature
- Email: hello@1nguoi.com

## 📄 License

Mọi đóng góp sẽ nằm dưới license GPL v3 của dự án.
