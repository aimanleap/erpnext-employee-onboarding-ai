# employee_onboarding/employee_onboarding/api/ai.py

import openai
import frappe
from frappe.utils import today, add_days

def get_openai_api_key():
    """Fetch API key from site_config.json"""
    api_key = frappe.conf.get("OPENAI_API_KEY")
    if not api_key:
        frappe.throw("OpenAI API Key not found in site_config.json")
    return api_key

openai.api_key = get_openai_api_key()

def generate_checklist(role):
    prompt = f"""
    Generate an onboarding checklist for a {role}. Include department-wise tasks.
    Format your response as JSON array of objects like:
    [
      {{
        "description": "Task description",
        "department": "Department name"
      }},
      ...
    ]
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an HR assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        content = response.choices[0].message.content.strip()
        return eval(content)  # ⚠️ Only safe if input is controlled
    except Exception as e:
        frappe.throw(f"Error generating checklist: {str(e)}")
        return []

def classify_risk_level(comment):
    prompt = f"""
    Classify the sentiment of this comment as Low/Medium/High risk:
    "{comment}"
    Only return one word: Low / Medium / High
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an HR assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        frappe.throw(f"Error classifying risk: {str(e)}")
        return "Low"

def predict_asset_demand():
    """
    Predict asset demand based on upcoming onboardings.
    Returns a dictionary with predicted demand per asset type.
    """
    upcoming_date = add_days(today(), 7)

    onboardings = frappe.get_all("Employee Onboarding Tracker",
        filters={
            "joining_date": ["<=", upcoming_date],
            "status": ["!=", "Completed"]
        },
        fields=["required_assets"]
    )

    asset_demand = {}

    for onboarding in onboardings:
        if onboarding.required_assets:
            assets = frappe.get_all("Employee Onboarding Asset",
                filters={"parent": onboarding.name},
                fields=["asset_type", "quantity"]
            )
            for asset in assets:
                asset_demand[asset.asset_type] = asset_demand.get(asset.asset_type, 0) + asset.quantity

    return asset_demand

def daily_onboarding_forecast():
    """
    Daily scheduled job to check upcoming onboardings
    and trigger asset demand prediction or alerts.
    """
    upcoming_date = add_days(today(), 7)
    onboardings = frappe.get_all(
        "Employee Onboarding Tracker",
        filters={
            "joining_date": ["<=", upcoming_date],
            "status": ["!=", "Completed"]
        },
        fields=["name", "joining_date", "required_assets"]
    )

    if onboardings:
        predicted_demand = predict_asset_demand()
        frappe.log_error("Daily Forecast", f"Predicted Asset Demand: {predicted_demand}")
        # TODO: Add logic to compare with actual stock and alert if shortage

def handle_onboarding_created(doc, method):
    frappe.log_error("Onboarding Created", f"New onboarding created: {doc.name}")
    # You can add logic here like:
    # - Trigger AI checklist generation
    # - Notify departments

def test_ai_connection(prompt="What is 1 + 1?"):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        answer = response.choices[0].message.content.strip()
        return answer
    except Exception as e:
        frappe.throw(f"❌ AI Error: {str(e)}")