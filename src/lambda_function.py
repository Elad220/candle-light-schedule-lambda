import json
import os
from datetime import datetime, timedelta

import boto3
import pytz
import requests
from aws_lambda_powertools import Logger

class EventBridgeRuleCreationError(Exception):
    """Exception raised when an error occurs creating an EventBridge rule."""

    pass


class EventBridgeTargetCreationError(Exception):
    """Exception raised when an error occurs creating an EventBridge target."""

    pass

TRIGGER_LAMBDA_NAME = os.environ["TRIGGER_LAMBDA_NAME"]
TRIGGER_LAMBDA_ARN = os.environ["TRIGGER_LAMBDA_ARN"]
EVENTBRIDGE_IAM_ROLE = os.environ["EVENTBRIDGE_IAM_ROLE"]
URL = "https://www.hebcal.com/shabbat?cfg=json&geonameid=293397&M=on"

logger = Logger()


def get_candle_time():
    try:
        response = requests.get(URL)
        response.raise_for_status()
        json_response = response.json()
        for item in json_response["items"]:
            if item["category"] == "candles":
                candle_time = item["date"]
                break
        return datetime.strptime(candle_time, "%Y-%m-%dT%H:%M:%S%z")
    except requests.exceptions.HTTPError as errh:
        logger.error(f"HTTP Error: {errh}")
    except requests.exceptions.ConnectionError as errc:
        logger.error(f"Error Connecting: {errc}")
    except requests.exceptions.Timeout as errt:
        logger.error(f"Timeout Error: {errt}")
    except requests.exceptions.RequestException as err:
        logger.error(f"Something went wrong: {err}")
    return None


def lambda_handler(event, context):
    schedules_list = []
    utc = pytz.utc
    candle_time = get_candle_time()
    candle_time_delta_ten = (candle_time - timedelta(minutes=10)).astimezone(utc).time()
    candle_time_delta_five = (candle_time - timedelta(minutes=5)).astimezone(utc).time()
    if candle_time_delta_ten and candle_time_delta_five:
        logger.debug("received candle lighting time")
        client = boto3.client("events")
        schedules_list.append(
            f"cron({candle_time_delta_ten.minute} {candle_time_delta_ten.hour} ? * fri *)"
        )
        schedules_list.append(
            f"cron({candle_time_delta_five.minute} {candle_time_delta_five.hour} ? * fri *)"
        )

        for i, schedule_expression in enumerate(schedules_list):
            logger.debug("Creating EventBridge rule {i}")
            if i == 0:
                mins = 10
            else:
                mins = 5

            response = client.put_rule(
                Name=f"schedule_expression_{i}",
                ScheduleExpression=schedule_expression,
                State="ENABLED",
                Description=f"EventBridge rule for {TRIGGER_LAMBDA_NAME} lambda function",
                RoleArn=EVENTBRIDGE_IAM_ROLE,
            )
            if response["ResponseMetadata"]["HTTPStatusCode"] != 200:
                raise EventBridgeRuleCreationError(
                    f"Failed to create EventBridge rule {i}. Response: {response}"
                )
            logger.debug(f"created eventbridge rule {i} for {schedule_expression}")

            response = client.put_targets(
                Rule=f"schedule_expression_{i}",
                Targets=[
                    {
                        "Id": f"{TRIGGER_LAMBDA_NAME}",
                        "Arn": f"{TRIGGER_LAMBDA_ARN}",
                        "Input": json.dumps(
                            {
                                "candle_time": datetime.isoformat(candle_time),
                                "scheduled_for": mins,
                            }
                        ),
                    }
                ],
            )
            if response["ResponseMetadata"]["HTTPStatusCode"] != 200:
                raise EventBridgeTargetCreationError(
                    f"Failed to create EventBridge rule {i}. Response: {response}"
                )
            logger.debug(f"created eventbridge target for rule {i}")
            logger.info(f"EventBridge rule {i} created successfully!")

        return {"statusCode": 200, "body": "EventBridge rule created successfully!"}

    else:
        logger.error("No candle lighting time found.")
