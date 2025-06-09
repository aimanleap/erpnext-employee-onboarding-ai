frappe.ui.form.on('Employee Onboarding Tracker', {
    refresh(frm) {
        frm.add_custom_button(__('Test Slack'), function () {
            frappe.call({
                method: 'employee_onboarding.api.ai.send_slack_notification',
                args: {
                    message: '🔔 Test button clicked in ERPNext!'
                },
                callback(r) {
                    if (!r.exc) {
                        frappe.msgprint("Slack message sent!");
                    } else {
                        frappe.msgprint("Failed to send Slack message.");
                    }
                }
            });
        }, __("AI Actions"));
    }
});