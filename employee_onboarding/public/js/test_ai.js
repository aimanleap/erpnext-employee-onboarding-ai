frappe.ui.form.on("Employee Onboarding Tracker", {
    refresh(frm) {
        frm.add_custom_button(
            "Test Button",
            function () {
                console.log("✅ Button clicked!");
            },
            "Test Tools"
        );
    }
});