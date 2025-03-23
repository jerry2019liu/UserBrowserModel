# model.py
# user browser model with cloud watch click stream data

import pandas as pd
import numpy as np
import boto3
import json
from datetime import datetime

# --- AWS Configuration ---
AWS_REGION = 'your_aws_region'  # e.g., 'us-east-1'
LOG_GROUP_NAME = 'your_log_group_name'  # e.g., '/aws/lambda/your-clickstream-function'
LOG_STREAM_PREFIX = 'your_log_stream_prefix'  # Optional: filter by prefix
PROFILE_NAME = 'your_aws_profile' # Optional: if using named profiles
START_TIME = datetime(2023, 1, 1)  # Example start time
END_TIME = datetime.now()

# --- Initialize AWS Resources ---
if PROFILE_NAME:
    session = boto3.Session(profile_name=PROFILE_NAME, region_name=AWS_REGION)
else:
    session = boto3.Session(region_name=AWS_REGION)

logs_client = session.client('logs')

def extract_clickstream_data(log_events):
    """Extracts relevant clickstream data from CloudWatch Logs events."""
    extracted_data = []
    for event in log_events:
        message = event['message']
        try:
            # Assuming clickstream data is in JSON format within the message
            data = json.loads(message)

            # Example: Extracting user ID, timestamp, page URL, and browser info
            user_id = data.get('userId')
            timestamp = datetime.fromtimestamp(event['timestamp'] / 1000.0)  # Convert milliseconds to seconds
            page_url = data.get('pageUrl')
            browser = data.get('browser') # e.g. chrome, firefox, safari
            os = data.get('os') # e.g. windows, macos, linux, android, ios
            device = data.get('device') # e.g. desktop, mobile, tablet
            if user_id and page_url and browser:
                extracted_data.append({
                    'userId': user_id,
                    'timestamp': timestamp,
                    'pageUrl': page_url,
                    'browser': browser,
                    'os': os,
                    'device': device,
                })

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            print(f"Error processing log message: {message}. Error: {e}")
            continue

    return extracted_data

def get_cloudwatch_logs(log_group_name, start_time, end_time, log_stream_prefix=None):
    """Retrieves log events from CloudWatch Logs."""
    log_events = []
    next_token = None

    start_time_ms = int(start_time.timestamp() * 1000)
    end_time_ms = int(end_time.timestamp() * 1000)

    while True:
        params = {
            'logGroupName': log_group_name,
            'startTime': start_time_ms,
            'endTime': end_time_ms,
            'limit': 10000,
        }
        if log_stream_prefix:
            params['logStreamNamePrefix'] = log_stream_prefix

        if next_token:
            params['nextToken'] = next_token

        response = logs_client.filter_log_events(**params)
        log_events.extend(response['events'])

        next_token = response.get('nextToken')
        if not next_token:
            break

    return log_events

# --- Main Execution ---
log_events = get_cloudwatch_logs(LOG_GROUP_NAME, START_TIME, END_TIME, LOG_STREAM_PREFIX)
clickstream_data = extract_clickstream_data(log_events)

if clickstream_data:
    df = pd.DataFrame(clickstream_data)

    # --- User Browser Model ---
    user_browser_usage = df.groupby('userId')['browser'].value_counts(normalize=True).unstack(fill_value=0)
    user_os_usage = df.groupby('userId')['os'].value_counts(normalize=True).unstack(fill_value=0)
    user_device_usage = df.groupby('userId')['device'].value_counts(normalize=True).unstack(fill_value=0)

    print("User Browser Usage:")
    print(user_browser_usage)
    print("\nUser OS Usage:")
    print(user_os_usage)
    print("\nUser Device Usage:")
    print(user_device_usage)

    # --- Further Analysis (Optional) ---
    # Example: Most popular browsers overall
    overall_browser_usage = df['browser'].value_counts(normalize=True)
    print("\nOverall Browser Usage:")
    print(overall_browser_usage)

    # Example: Most popular os overall
    overall_os_usage = df['os'].value_counts(normalize=True)
    print("\nOverall OS Usage:")
    print(overall_os_usage)

    # Example: Most popular device overall
    overall_device_usage = df['device'].value_counts(normalize=True)
    print("\nOverall Device Usage:")
    print(overall_device_usage)

    # Example: Time-based analysis
    df['hour'] = df['timestamp'].dt.hour
    hourly_browser_usage = df.groupby('hour')['browser'].value_counts(normalize=True).unstack(fill_value=0)
    print("\nHourly Browser Usage:")
    print(hourly_browser_usage)

else:
    print("No clickstream data found.")
