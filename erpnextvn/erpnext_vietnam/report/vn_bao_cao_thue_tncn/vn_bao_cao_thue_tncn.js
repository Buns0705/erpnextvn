frappe.query_reports["VN Báo Cáo Thuế TNCN"] = {
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
            fieldname: "from_date",
            label: __("Từ ngày"),
            fieldtype: "Date",
            default: frappe.datetime.year_start(),
            reqd: 1,
        },
        {
            fieldname: "to_date",
            label: __("Đến ngày"),
            fieldtype: "Date",
            default: frappe.datetime.get_today(),
            reqd: 1,
        },
    ],
};
