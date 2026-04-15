frappe.query_reports["VN Sổ Cái"] = {
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
            fieldname: "account",
            label: __("Tài khoản"),
            fieldtype: "Link",
            options: "Account",
            reqd: 1,
            get_query: function () {
                return {
                    filters: {
                        company: frappe.query_report.get_filter_value("company"),
                        is_group: 0,
                    },
                };
            },
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
