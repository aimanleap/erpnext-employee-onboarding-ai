// employee_onboarding/public/js/test_button.js

console.log("✅ test_button.js loaded");

frappe.ui.form.on("Employee Onboarding Tracker", {
    refresh(frm) {
        console.log("🧾 Form refreshed");

        // Ensure the document is saved before showing the button
        if (!frm.is_new()) {
            console.log("🔘 Adding Test Button...");

            frm.add_custom_button(
                __("Test Button"),
                function () {
                    try {
                        console.log("🎉 Button clicked!");
                        frappe.msgprint("🎉 Button clicked from JS file!");
                    } catch (err) {
                        console.error("❌ Error in button handler:", err);
                    }
                },
                __("Test Tools")
            );
        }
    }
});