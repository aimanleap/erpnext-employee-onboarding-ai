# ERPNext Employee Onboarding Automation with AI Integration

A custom ERPNext app that automates employee onboarding using AI-powered features like checklist generation, asset demand prediction, sentiment analysis, and Slack alerts.

##  Features

-  Custom Doctype: `Employee Onboarding Tracker`
-  AI Checklist Generation (OpenAI)
-  Predict Asset Demand vs Stock
-  Candidate Risk Level Detection via Sentiment Analysis
-  Slack Alerts for Shortages
-  Draft Material Request Auto-Creation
-  Real-Time Dashboard in ERPNext

##  Tech Stack

- ERPNext v15
- Frappe Framework
- Python 3.x
- OpenAI GPT API
- Slack Webhooks
- JavaScript (Client-side logic)

##  Project Structure
employee_onboarding/
├── employee_onboarding/
│   ├── hooks.py
│   ├── modules.txt
│   ├── public/
│   │   └── js/
│   │       └── ai_integration.js
│   ├── doctype/
│   │   └── employee_onboarding_tracker/
│   │       ├── *.py, *.json, *.js
│   ├── api/
│   │   └── ai.py
│   └── ...
├── README.md
├── requirements.txt
└── setup.py



### Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch develop
bench install-app employee_onboarding
```

 Set Required Configurations

```bash
bench set-config OPENAI_API_KEY "your_openai_key"
bench set-config SLACK_WEBHOOK_URL "your_slack_webhook"
```
Migrate and Restart
```bash
bench migrate
bench restart
```

### Testing 

After installation: 

    Go to ERPNext > Employee Onboarding Tracker 
    Fill in:
        Job Title  → Click Generate Checklist  (AI-generated tasks appear)
        Candidate Comment  → Click Classify Risk Level 
        Add assets in Required Assets  table
         
    Save form → AI checks for stock shortage and sends alert to Slack
    If stock is low, a Draft Material Request  is created automatically
     


### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/employee_onboarding
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade

### License

mit
