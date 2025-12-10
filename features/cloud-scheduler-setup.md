# Cloud Scheduler Setup for AgentX

This guide explains how to set up automated, scheduled rule runs using Google Cloud Scheduler and Pub/Sub.

## Architecture

```
Cloud Scheduler → Pub/Sub Topic → Cloud Function → AgentX Backend API
```

## Step 1: Enable Cloud Scheduler API

```bash
gcloud services enable cloudscheduler.googleapis.com
gcloud services enable pubsub.googleapis.com
gcloud services enable cloudfunctions.googleapis.com
```

## Step 2: Create Pub/Sub Topic

```bash
PROJECT_ID=hackathon-practice-480508

# Create topic for rule execution
gcloud pubsub topics create agentx-rule-scheduler --project $PROJECT_ID

# Create subscription
gcloud pubsub subscriptions create agentx-rule-sub \
  --topic agentx-rule-scheduler \
  --project $PROJECT_ID
```

## Step 3: Create Cloud Function (Webhook Handler)

Create a simple Cloud Function that receives Pub/Sub messages and calls the AgentX API.

**File: `functions/scheduler_handler/main.py`**:

```python
import json
import requests
import base64
from flask import Flask, request

BACKEND_URL = "https://agentx-backend-783063936000.us-central1.run.app"

def pubsub_handler(event, context):
    """
    Triggered from a Pub/Sub message.
    Executes scheduled rule runs.
    """
    pubsub_message = base64.b64decode(event['data']).decode('utf-8')
    message_data = json.loads(pubsub_message)
    
    rule_id = message_data.get('rule_id')
    
    if not rule_id:
        print("No rule_id in message")
        return
    
    print(f"Running scheduled rule: {rule_id}")
    
    # Call AgentX API to run the rule
    payload = {
        "rule_id": rule_id,
        "limit": 200
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/run-rule", json=payload)
        if response.status_code == 200:
            result = response.json()
            print(f"Success: {result}")
        else:
            print(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Failed to run rule: {e}")
```

**File: `functions/scheduler_handler/requirements.txt`**:

```
requests
flask
```

## Step 4: Deploy Cloud Function

```bash
gcloud functions deploy agentx-scheduler-handler \
  --runtime python310 \
  --trigger-topic agentx-rule-scheduler \
  --entry-point pubsub_handler \
  --region us-central1 \
  --project $PROJECT_ID \
  --service-account agentx-backend-sa@$PROJECT_ID.iam.gserviceaccount.com
```

## Step 5: Create Cloud Scheduler Jobs

### Daily Rule Run (Every day at 2 AM)

```bash
gcloud scheduler jobs create pubsub daily-dq-check \
  --location us-central1 \
  --schedule "0 2 * * *" \
  --topic agentx-rule-scheduler \
  --message-body '{"rule_id": "R001", "schedule": "daily"}' \
  --project $PROJECT_ID
```

### Hourly Rule Run (Every hour)

```bash
gcloud scheduler jobs create pubsub hourly-dq-check \
  --location us-central1 \
  --schedule "0 * * * *" \
  --topic agentx-rule-scheduler \
  --message-body '{"rule_id": "R002", "schedule": "hourly"}' \
  --project $PROJECT_ID
```

### Weekly Rule Run (Every Monday at 9 AM)

```bash
gcloud scheduler jobs create pubsub weekly-dq-check \
  --location us-central1 \
  --schedule "0 9 * * 1" \
  --topic agentx-rule-scheduler \
  --message-body '{"rule_id": "R003", "schedule": "weekly"}' \
  --project $PROJECT_ID
```

## Step 6: Test the Scheduler

### Manually trigger a job

```bash
gcloud scheduler jobs run daily-dq-check \
  --location us-central1 \
  --project $PROJECT_ID
```

### View logs

```bash
gcloud logging read "resource.type=cloud_function AND resource.labels.function_name=agentx-scheduler-handler" \
  --limit 50 \
  --format json \
  --project $PROJECT_ID
```

## Step 7: List and Manage Jobs

### List all jobs

```bash
gcloud scheduler jobs list --location us-central1 --project $PROJECT_ID
```

### Pause a job

```bash
gcloud scheduler jobs pause daily-dq-check --location us-central1 --project $PROJECT_ID
```

### Resume a job

```bash
gcloud scheduler jobs resume daily-dq-check --location us-central1 --project $PROJECT_ID
```

### Delete a job

```bash
gcloud scheduler jobs delete daily-dq-check --location us-central1 --project $PROJECT_ID
```

## Advanced: Add Notification on Failure

Create an alerting policy to notify when rules fail:

```bash
# Create an alert when Cloud Function fails
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="AgentX Scheduler Failures" \
  --condition-display-name="Function Errors" \
  --condition-threshold-value=1 \
  --condition-threshold-duration=60s \
  --project $PROJECT_ID
```

## Cost Considerations

- **Cloud Scheduler**: $0.10 per job per month (first 3 jobs free)
- **Pub/Sub**: First 10 GB/month free
- **Cloud Functions**: First 2 million invocations free per month
- **Example**: 3 scheduled jobs = **FREE** (within free tier)

## Monitoring

View scheduler job history in the Cloud Console:
https://console.cloud.google.com/cloudscheduler?project=hackathon-practice-480508

## Integration with AgentX UI

Add to the Streamlit frontend to manage scheduled jobs:

```python
import subprocess

def create_scheduled_rule(rule_id, schedule_cron):
    """
    Create a new Cloud Scheduler job for a rule
    """
    job_name = f"rule-{rule_id}-scheduled"
    message = json.dumps({"rule_id": rule_id, "schedule": "custom"})
    
    cmd = [
        "gcloud", "scheduler", "jobs", "create", "pubsub", job_name,
        "--location", "us-central1",
        "--schedule", schedule_cron,
        "--topic", "agentx-rule-scheduler",
        "--message-body", message,
        "--project", "hackathon-practice-480508"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0
```

## Troubleshooting

1. **Job doesn't run**: Check IAM permissions for service account
2. **Function fails**: View logs with `gcloud functions logs read`
3. **API errors**: Verify backend URL and rule_id exist
4. **Pub/Sub issues**: Check subscription and topic configuration

---

**Next Steps:**
- Test manual execution first
- Start with one daily job
- Monitor for 1 week before adding more schedules
- Set up alerting for failures

