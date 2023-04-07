import os
import json
import boto3
import pytest
from moto import mock_events, mock_lambda
from datetime import datetime

from src.lambda_function import lambda_handler

TRIGGER_LAMBDA_NAME = os.environ["TRIGGER_LAMBDA_NAME"]
TRIGGER_LAMBDA_ARN = os.environ["TRIGGER_LAMBDA_ARN"]
EVENTBRIDGE_IAM_ROLE = os.environ["EVENTBRIDGE_IAM_ROLE"]

@pytest.fixture
def event():
    return {}

@pytest.fixture
def context():
    return {}

@mock_events
@mock_lambda
def test_lambda_handler(event, context):
    # Mock the response from the external API
    candle_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S%z")
    response = {
        "items": [
            {
                "category": "candles",
                "date": candle_time
            }
        ]
    }
    eventbridge_client = boto3.client("events", region_name="us-east-1")
    # Create the EventBridge rule
    eventbridge_client.put_rule(
        Name="schedule_expression_0",
        ScheduleExpression="cron(50 18 ? * fri *)",
        State="ENABLED",
        Description=f"EventBridge rule for {TRIGGER_LAMBDA_NAME} lambda function",
        RoleArn=EVENTBRIDGE_IAM_ROLE,
    )
    # Create the EventBridge target
    eventbridge_client.put_targets(
        Rule="schedule_expression_0",
        Targets=[
            {
                "Id": TRIGGER_LAMBDA_NAME,
                "Arn": TRIGGER_LAMBDA_ARN,
                "Input": json.dumps(
                    {
                        "candle_time": candle_time,
                        "scheduled_for": 10,
                    }
                ),
            }
        ],
    )
    # Call the Lambda function
    result = lambda_handler(event, context)
    # Check that the response from the function is correct
    assert result["statusCode"] == 200
    assert result["body"] == "EventBridge rule created successfully!"
