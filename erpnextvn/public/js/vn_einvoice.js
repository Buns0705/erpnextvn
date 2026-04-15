// Sales Invoice — Vietnamese e-invoice publish/cancel buttons.

frappe.ui.form.on("Sales Invoice", {
    refresh(frm) {
        if (frm.doc.docstatus === 1 && !frm.doc.vn_einvoice_number) {
            frm.add_custom_button(
                __("Phát hành HĐĐT"),
                function () {
                    frappe.confirm(
                        __("Bạn có chắc muốn phát hành hóa đơn điện tử cho {0}?", [frm.doc.name]),
                        function () {
                            frappe.call({
                                method: "erpnextvn.e_invoicing.utils.send_einvoice",
                                args: { sales_invoice: frm.doc.name },
                                freeze: true,
                                freeze_message: __("Đang phát hành hóa đơn điện tử..."),
                                callback: function (r) {
                                    if (r.message) {
                                        frappe.show_alert({
                                            message: __("Đã phát hành HĐĐT số: {0}", [
                                                r.message.invoice_number || "",
                                            ]),
                                            indicator: "green",
                                        });
                                        frm.reload_doc();
                                    }
                                },
                            });
                        }
                    );
                },
                __("Hóa đơn điện tử")
            );
        }

        if (frm.doc.vn_einvoice_status === "Đã phát hành" && frm.doc.vn_einvoice_number) {
            frm.add_custom_button(
                __("Hủy HĐĐT"),
                function () {
                    frappe.prompt(
                        {
                            fieldname: "reason",
                            fieldtype: "Small Text",
                            label: __("Lý do hủy"),
                            reqd: 1,
                        },
                        function (values) {
                            frappe.call({
                                method: "erpnextvn.e_invoicing.utils.cancel_einvoice",
                                args: {
                                    sales_invoice: frm.doc.name,
                                    reason: values.reason,
                                },
                                freeze: true,
                                freeze_message: __("Đang hủy hóa đơn điện tử..."),
                                callback: function () {
                                    frm.reload_doc();
                                },
                            });
                        },
                        __("Hủy hóa đơn điện tử"),
                        __("Xác nhận hủy")
                    );
                },
                __("Hóa đơn điện tử")
            );
        }
    },
});
