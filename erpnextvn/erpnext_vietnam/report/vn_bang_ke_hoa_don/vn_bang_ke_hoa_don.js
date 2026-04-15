frappe.query_reports["VN Bảng Kê Hóa Đơn"] = {
    filters: [
        {
            fieldname: "company",
            label: __("Công ty"),
            fieldtype: "Link",
            options: "Company",
            default: frappe.defaults.get_user_default("Company"),
            reqd: 1,
        },
        {
            fieldname: "invoice_type",
            label: __("Loại hóa đơn"),
            fieldtype: "Select",
            options: "Sales\nPurchase",
            default: "Sales",
            reqd: 1,
        },
        {
            fieldname: "from_date",
            label: __("Từ ngày"),
            fieldtype: "Date",
            default: frappe.datetime.month_start(),
            reqd: 1,
        },
        {
            fieldname: "to_date",
            label: __("Đến ngày"),
            fieldtype: "Date",
            default: frappe.datetime.month_end(),
            reqd: 1,
        },
    ],
};
