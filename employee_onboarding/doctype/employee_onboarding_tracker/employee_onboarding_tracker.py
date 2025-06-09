# employee_onboarding/doctype/employee_onboarding_tracker/employee_onboarding_tracker.py

import frappe
from frappe.model.document import Document
from employee_onboarding.api.ai import (
    generate_checklist,
    predict_asset_demand,
    classify_risk_level,
    send_slack_notification,
    check_current_stock,
    trigger_material_request
)

class EmployeeOnboardingTracker(Document):

    def validate(self):
        self.set_joining_date_from_employee()
        self.generate_checklist_if_empty()
        self.classify_candidate_risk_level()

    def set_joining_date_from_employee(self):
        if self.employee and not self.joining_date:
            try:
                emp = frappe.get_doc("Employee", self.employee)
                if emp.date_of_joining:
                    self.joining_date = emp.date_of_joining
            except Exception as e:
                frappe.log_error(f"Error setting joining date: {str(e)}")

    def generate_checklist_if_empty(self):
        if not self.checklist and self.job_title:
            try:
                tasks = generate_checklist(self.job_title)
                for task in tasks:
                    if task["department"]:  # skip tasks without valid department
                        self.append("checklist", {
                            "task_description": task["description"],
                            "department": task["department"]
                        })
            except Exception as e:
                frappe.log_error(f"Error generating checklist: {str(e)}")

    def classify_candidate_risk_level(self):
        if self.candidate_comment and not self.risk_level:
            try:
                risk = classify_risk_level(self.candidate_comment)
                self.risk_level = risk
            except Exception as e:
                frappe.log_error(f"Risk classification failed: {e}")

    def on_update(self):
        """
        Triggered every time the document is saved.
        We add a flag to avoid duplicate execution.
        """
        if not hasattr(self, "_asset_check_done"):
            frappe.log_error("on_update triggered", "Lifecycle Debug")
            self.notify_departments()
            self.predict_and_alert_asset_shortage()
            self._asset_check_done = True  # Prevent duplicate runs

    def notify_departments(self):
        # Placeholder for future email or workflow-based notifications
        pass

    def predict_and_alert_asset_shortage(self):
        try:
            asset_forecast = predict_asset_demand()
            for asset_name, required_qty in asset_forecast.items():
                available_qty = check_current_stock(asset_name)
                if available_qty < required_qty:
                    shortage = required_qty - available_qty
                    message = f"""
⚠️ *Asset Shortage Alert*
Asset: *{asset_name}*
Required: {required_qty}
Available: {available_qty}
Shortage: {shortage}
Consider creating a material request.
                    """
                    send_slack_notification(message)
                    mr_name = trigger_material_request(asset_name, shortage)
                    if mr_name:
                        message += f"\n✅ Draft MR created: `{mr_name}`"
                        send_slack_notification(message)
        except Exception as e:
            frappe.log_error(f"Error in predict_and_alert_asset_shortage: {str(e)}")