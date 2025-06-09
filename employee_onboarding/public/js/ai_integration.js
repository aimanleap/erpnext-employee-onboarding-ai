// public/js/ai_integration.js

frappe.ui.form.on("Employee Onboarding Tracker", {
    refresh(frm) {
        if (!frm.is_new()) {
            // === Generate Checklist Button ===
            frm.add_custom_button(
                __("Generate Checklist"),
                function () {
                    if (!frm.doc.job_title) {
                        frappe.msgprint(__("Please enter a Job Title first."));
                        return;
                    }

                    frappe.call({
                        method: "employee_onboarding.api.ai.generate_checklist",
                        args: { role: frm.doc.job_title },
                        callback(r) {
                            if (r.message && r.message.length > 0) {
                                frm.clear_table("checklist");
                                r.message.forEach((task) => {
                                    let row = frm.add_child("checklist");
                                    row.task_description = task.description;
                                    row.department = task.department;
                                });
                                frm.refresh_field("checklist");
                                frappe.show_alert(
                                    { message: __("Checklist generated successfully!"), indicator: "green" }
                                );
                            } else {
                                frappe.show_alert(
                                    { message: __("No tasks returned from AI."), indicator: "orange" }
                                );
                            }
                        },
                        error(r) {
                            frappe.show_alert(
                                { message: __("Failed to generate checklist."), indicator: "red" }
                            );
                        }
                    });
                },
                __("AI Actions")
            );

            // === Classify Risk Level Button ===
            frm.add_custom_button(
                __("Classify Risk Level"),
                function () {
                    if (!frm.doc.candidate_comment) {
                        frappe.msgprint(__("Please enter a Candidate Comment first."));
                        return;
                    }

                    frappe.show_progress(__("Analyzing Sentiment..."), 0, 100);

                    frappe.call({
                        method: "employee_onboarding.api.ai.classify_candidate_risk_level",
                        args: { comment: frm.doc.candidate_comment },
                        callback(r) {
                            if (r.message) {
                                frm.set_value("risk_level", r.message);
                                frappe.hide_progress();
                                frappe.show_alert({
                                    message: __("Candidate risk level classified as: ") + r.message,
                                    indicator:
                                        r.message === "High"
                                            ? "red"
                                            : r.message === "Medium"
                                              ? "orange"
                                              : "green",
                                });
                            } else {
                                frappe.show_alert(
                                    { message: __("Failed to classify risk level."), indicator: "red" }
                                );
                            }
                        },
                        error(r) {
                            frappe.hide_progress();
                            frappe.show_alert(
                                { message: __("Failed to classify risk level."), indicator: "red" }
                            );
                        }
                    });
                },
                __("AI Actions")
            );
        }
    },

    after_save(frm) {
        //  Trigger shortage check automatically on save
        frappe.call({
            method: "employee_onboarding.api.ai.check_and_alert_asset_shortage",
            args: { docname: frm.doc.name },
            callback(r) {
                if (r.message) {
                    console.log("Asset shortage check completed:", r.message);
                }
            }
        });
    },

    candidate_comment(frm) {
        if (frm.doc.candidate_comment && !frm.doc.risk_level) {
            frappe.call({
                method: "employee_onboarding.api.ai.classify_candidate_risk_level",
                args: { comment: frm.doc.candidate_comment },
                callback(r) {
                    if (r.message) {
                        frm.set_value("risk_level", r.message);
                    }
                }
            });
        }
    }
});