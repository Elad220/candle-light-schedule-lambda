import os
import requests
import boto3
from datetime import datetime, timedelta
import logging
import json
import pytz

TRIGGER_LAMBDA_NAME = os.environ["TRIGGER_LAMBDA_NAME"]
TRIGGER_LAMBDA_ARN = os.environ["TRIGGER_LAMBDA_ARN"]
EVENTBRIDGE_IAM_ROLE = os.environ["EVENTBRIDGE_IAM_ROLE"]
URL = "https://www.hebcal.com/shabbat?cfg=json&geonameid=293397&M=on"

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)-8s %(message)s"))
logging.getLogger().addHandler(handler)


def get_candle_time():
    try:
        response = requests.get(URL)
        response.raise_for_status()
        json_response = response.json()
        for item in json_response["items"]:
            if item["category"] == "candles":
                candle_time = item["date"]
                break
        # candle_time = candle_time.split("+")[0]
        return datetime.strptime(candle_time, "%Y-%m-%dT%H:%M:%S%z")
    except requests.exceptions.HTTPError as errh:
        logging.error(f"HTTP Error: {errh}")
    except requests.exceptions.ConnectionError as errc:
        logging.error(f"Error Connecting: {errc}")
    except requests.exceptions.Timeout as errt:
        logging.error(f"Timeout Error: {errt}")
    except requests.exceptions.RequestException as err:
        logging.error(f"Something went wrong: {err}")
    return None


def lambda_handler(event, context):
    schedules_list = []
    utc = pytz.utc
    candle_time = get_candle_time()
    candle_time_delta_ten = (candle_time - timedelta(minutes=10)).astimezone(utc).time()
    candle_time_delta_five = (candle_time - timedelta(minutes=5)).astimezone(utc).time()
    if candle_time_delta_ten and candle_time_delta_five:
        logging.info("received candle lighting time")
        client = boto3.client("events")
        schedules_list.append(
            f"cron({candle_time_delta_ten.minute} {candle_time_delta_ten.hour} ? * fri *)"
        )
        schedules_list.append(
            f"cron({candle_time_delta_five.minute} {candle_time_delta_five.hour} ? * fri *)"
        )

        for i, schedule_expression in enumerate(schedules_list):
            logging.info("Creating EventBridge rule {i}")
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
            logging.info(f"EventBridge rule {i} created successfully!")

        return {"statusCode": 200, "body": "EventBridge rule created successfully!"}

    else:
        logging.error("No candle lighting time found.")
