app_name = "employee_onboarding"
app_title = "employee_onboarding"
app_publisher = "Ai Man"
app_description = "AI-Powered Employee Onboarding Automation"
app_email = "aimanleap@gmail.com"
app_license = "mit"

doc_events = {
    "Employee Onboarding Tracker": {
        "after_insert": "employee_onboarding.api.ai.handle_onboarding_created"
    }
}

scheduler_events = {
    "daily": [
        "employee_onboarding.api.ai.daily_onboarding_forecast"
    ]
}

# Load JS file for AI integration
doctype_js = {
    #"Employee Onboarding Tracker": "public/js/test_ai.js"
    #"Employee Onboarding Tracker": "public/js/test_button.js"
    "Employee Onboarding Tracker": "./public/js/ai_integration.js"
    #"Employee Onboarding Tracker": "./public/js/slack.js"
}

def handle_onboarding_created(doc, method):
    # Trigger any post-insert logic
    pass

def daily_onboarding_forecast():
    # Run daily predictions and alerts
    pass

app_include_js = "/assets/employee_onboarding/js/ai_integration.js"
#app_include_js = "/assets/employee_onboarding/js/slack.js"