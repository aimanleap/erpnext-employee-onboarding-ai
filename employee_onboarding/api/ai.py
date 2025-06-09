# employee_onboarding/employee_onboarding/api/ai.py

import os
import frappe
import json
import requests
from openai import OpenAI
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY") or frappe.conf.get("OPENAI_API_KEY")
)

SLACK_WEBHOOK_URL = frappe.conf.get("SLACK_WEBHOOK_URL")

# Map generic department names to ERPNext department names
DEPARTMENT_MAP = {
    "IT": "IT",
    "Human Resources": "HR",
    "Finance": "Accounts",
    "Procurement": "Purchase",
    "Training": "Training",
    "Administration": "Admin",
    "Engineering": "Engineering",
    "Marketing": "Marketing",
    "Sales": "Sales"
}


@frappe.whitelist()
def check_and_alert_asset_shortage(docname):
    """
    Triggered manually or via save to predict and alert asset shortages.
    """
    try:
        doc = frappe.get_doc("Employee Onboarding Tracker", docname)
        asset_forecast = {}
        for asset in doc.required_assets:
            asset_name = asset.asset_type
            asset_forecast[asset_name] = asset_forecast.get(asset_name, 0) + asset.quantity

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
        return "Asset check completed."
    except Exception as e:
        frappe.log_error(f"Error checking asset shortage: {str(e)}")
        return f"Error: {str(e)}"

@frappe.whitelist()
def generate_checklist(role):
    prompt = f"""
    Generate an onboarding checklist for a {role}. Include department-wise tasks.
    Return JSON array of objects like:
    [
      {{
        "description": "Task description",
        "department": "Mapped department name (e.g., IT, HR)"
      }},
      ...
    ]
    Only return valid departments from this list: {', '.join(DEPARTMENT_MAP.keys())}
    """

    try:
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an HR assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )

        content = completion.choices[0].message.content.strip()

        # Remove markdown if present
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]

        tasks = json.loads(content)

        # Map GPT's generic department names to ERPNext department codes
        for task in tasks:
            gpt_dept = task.get("department")
            erp_dept = DEPARTMENT_MAP.get(gpt_dept, None)
            if erp_dept and frappe.db.exists("Department", erp_dept):
                task["department"] = erp_dept
            else:
                task["department"] = None  # Skip invalid department

        return tasks

    except Exception as e:
        frappe.throw(f"Error generating checklist: {str(e)}")
        return []


@frappe.whitelist()
def classify_candidate_risk_level(comment):
    """
    Classify candidate comment into risk levels: Low / Medium / High
    """
    prompt = f"""
    Analyze the following candidate comment and classify the sentiment as:
    - Low Risk
    - Medium Risk
    - High Risk

    Candidate comment: "{comment}"

    ONLY respond with one word: Low, Medium, or High
    """

    try:
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an HR assistant analyzing candidate sentiment."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )

        risk_level = completion.choices[0].message.content.strip().capitalize()
        return risk_level

    except Exception as e:
        frappe.log_error(f"Error classifying risk level: {str(e)}")
        return "Low"  # Default fallback

def predict_asset_demand():
    """
    Predict asset demand based on upcoming onboardings and historical data.
    Returns a dictionary like {'Laptop': 5, 'Chair': 4}
    """
    today = datetime.today()
    next_month = today + timedelta(days=30)

    # Get upcoming onboardings in next 30 days
    upcoming = frappe.get_all("Employee Onboarding Tracker",
                              filters={"joining_date": ["between", [today.date(), next_month.date()]]},
                              fields=["name"])

    asset_demand = {}

    for record in upcoming:
        if not record.name:
            continue
        assets = frappe.get_all("Employee Onboarding Asset",
                                filters={"parent": record.name},
                                fields=["asset_type", "quantity"])
        for asset in assets:
            asset_name = asset.asset_type
            asset_demand[asset_name] = asset_demand.get(asset_name, 0) + asset.quantity

    return asset_demand


def check_current_stock(asset_name):
    """Check current available stock for an asset type using Bin"""
    item_code = frappe.db.get_value("Item", {"item_name": asset_name}, "item_code")
    if not item_code:
        frappe.log_error(f"Item not found for asset: {asset_name}")
        return 0

    bin_data = frappe.db.get_value("Bin", {"item_code": item_code}, ["actual_qty"], as_dict=True)
    return int(bin_data.actual_qty) if bin_data and bin_data.actual_qty else 0


def trigger_material_request(asset_name, quantity):
    """
    Create draft Material Request for missing assets.
    Returns MR name if successful, None otherwise.
    """

    # Try multiple ways to find a matching item
    item_code = frappe.db.get_value("Item", {"item_name": asset_name}, "item_code")
    if not item_code:
        # Fallback: try direct match by item_code (if asset_name is actually an item code)
        if frappe.db.exists("Item", asset_name):
            item_code = asset_name
        else:
            frappe.log_error(f"Item not found for asset: {asset_name}")
            return None

    try:
        mr = frappe.new_doc("Material Request")
        mr.material_request_type = "Purchase"
        item = mr.append("items")
        item.item_code = item_code
        item.qty = quantity
        item.schedule_date = datetime.today().date()
        mr.flags.ignore_permissions = True  # Ensure permissions don't block creation
        mr.save()

        frappe.log_error(f"Draft MR created: {mr.name} for {item_code} x{quantity}", "MR Creation")
        return mr.name

    except Exception as e:
        frappe.log_error(f"Error creating Material Request: {str(e)}", "MR Creation Error")
        return None


def send_slack_notification(message):
    """Send message to configured Slack channel"""
    if not SLACK_WEBHOOK_URL:
        frappe.log_error("Slack Webhook URL not configured.")
        return

    payload = {"text": message}
    try:
        response = requests.post(SLACK_WEBHOOK_URL, json=payload)
        if response.status_code != 200:
            frappe.log_error(f"Failed to send Slack message: {response.text}")
    except Exception as e:
        frappe.log_error(f"Error sending Slack message: {str(e)}")


def handle_onboarding_created(doc, method):
    frappe.log_error("New onboarding record created: {}".format(doc.name))

def daily_onboarding_forecast():
    """
    Daily background job to predict asset demand and notify Slack if shortages are expected.
    """
    frappe.logger().info("Running daily onboarding forecast job...")
    try:
        asset_forecast = predict_asset_demand()
        for asset_name, required_qty in asset_forecast.items():
            available_qty = check_current_stock(asset_name)
            if available_qty < required_qty:
                shortage = required_qty - available_qty
                message = f"""
                ⚠️ *Daily Forecast Alert*
                Asset: *{asset_name}*
                Required: {required_qty}
                Available: {available_qty}
                Shortage: {shortage}
                Consider placing a purchase order soon.
                """
                send_slack_notification(message)
    except Exception as e:
        frappe.logger().error(f"Error in daily_onboarding_forecast: {str(e)}")