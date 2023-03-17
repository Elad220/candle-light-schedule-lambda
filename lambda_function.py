import os
import requests
import boto3
from datetime import datetime, timedelta
import logging

BOT_TOKEN = os.environ['BOT_TOKEN']
BOT_CHATID = os.environ['BOT_CHATID']
TRIGGER_LAMBDA_NAME = os.environ['TRIGGER_LAMBDA_NAME']
TRIGGER_LAMBDA_ARN = os.environ['TRIGGER_LAMBDA_ARN']
URL = 'https://www.hebcal.com/shabbat?cfg=json&geonameid=293397&M=on'

logging.basicConfig(level=logging.INFO)

def send_message(message):
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    params = {'chat_id': BOT_CHATID, 'text': message}
    response = requests.post(url, data=params)
    response.raise_for_status()
    return response.json()

def get_candle_time():
    try:
        response = requests.get(URL)
        response.raise_for_status()
        json_response = response.json()
        for item in json_response['items']:
            if item['category'] == 'candles':
                candle_time = item['date']
                break
        candle_time = (candle_time.split('+')[0])
        candle_time_delta_ten = datetime.strptime(candle_time, '%Y-%m-%dT%H:%M:%S') - timedelta(minutes=10)
        candle_time_delta_five = datetime.strptime(candle_time, '%Y-%m-%dT%H:%M:%S') - timedelta(minutes=5)
        return candle_time_delta_ten, candle_time_delta_five
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
    candle_time_delta_ten, candle_time_delta_five = get_candle_time()
    if candle_time_delta_ten and candle_time_delta_five:
        client = boto3.client('events')
        schedule_expression_ten = f'cron({candle_time_delta_ten.minute} {candle_time_delta_ten.hour} ? * fri *)'
        schedule_expression_five = f'cron({candle_time_delta_five.minute} {candle_time_delta_five.hour} ? * fri *)'

        for schedule_expression in [schedule_expression_ten, schedule_expression_five]:
            response = client.put_rule(
                Name=f'schedule_expression_{schedule_expression}',
                ScheduleExpression=schedule_expression,
                State='ENABLED',
                Overwrite=True
            )

            response = client.put_targets(
                Rule=f'schedule_expression_{schedule_expression}',
                Targets=[
                    {
                        'Id': f"{TRIGGER_LAMBDA_NAME}",
                        'Arn': f'{TRIGGER_LAMBDA_ARN}',
                        'Input': '{}'
                    }
                ]
            )

        return {
            'statusCode': 200,
            'body': 'EventBridge rule created successfully!'
        }
    else:
        logging.error("No candle lighting time found.")


