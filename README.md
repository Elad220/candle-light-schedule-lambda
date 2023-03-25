# Candle Lighting Scheduler Lambda

This lambda is responsible of running every Friday at a fixed time, and then it creates 2 new schedules, 
it calculates the time 5 and 10 minutes before the candle lighting time, and creates an appropriate eventbridge rule schedule with those times.

## Requirements
1. Install the Python requirements using Poetry, then zip the lambda before upload
2. The following environment variables are necessary for the lambda to execute properly:

    a. TRIGGER_LAMBDA_NAME - the name of the alert lambda

    b. TRIGGER_LAMBDA_ARN - the ARN of the alert lambda

    c. EVENTBRIDGE_IAM_ROLE - the ARN of the appropriate IAM role which allows the lambda to create eventbridge rules.

3. Create an EventBridge schedule to execute this lambda every Friday at whatever time you choose.